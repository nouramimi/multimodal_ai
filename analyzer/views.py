"""
Views Django pour le chatbot multimodal - VERSION CORRIGÉE
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging
from moviepy import VideoFileClip
from PIL import Image
from .services.video_processor import VideoProcessor
from .services.chatbot_orchestrator import ImageAnalyzer

# ✅ CORRECTION: Import depuis services/
from .services.chatbot_orchestrator import MultimodalChatbot

logger = logging.getLogger(__name__)


@csrf_exempt
def send_message(request):
    """
    Endpoint pour envoyer un message au chatbot
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Récupérer les données
        text_message = request.POST.get('message', '').strip()
        images = request.FILES.getlist('images')
        videos = request.FILES.getlist('videos')
        session_id = request.session.session_key
        
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        logger.info(f"📨 Traitement du message: texte={bool(text_message)}, "
                   f"images={len(images)}, vidéos={len(videos)}")
        
        # Validation
        if not text_message and not images and not videos:
            return JsonResponse({
                'error': 'Message vide. Envoyez du texte, une image ou une vidéo.'
            }, status=400)
        
        # Initialiser le chatbot
        chatbot = MultimodalChatbot(session_id=session_id)
        
        # Traiter selon le type de contenu
        response_text = None
        
        # Cas 1: Texte seul
        if text_message and not images and not videos:
            logger.info("💬 Mode: Texte seul")
            response_text = chatbot.chat_text_only(text_message)
        
        # Cas 2: Texte + Image(s)
        elif images:
            logger.info(f"🖼️ Mode: Texte + {len(images)} image(s)")
            
            if len(images) == 1:
                # Une seule image - méthode optimisée
                image_data = images[0].read()
                response_text = chatbot.chat_with_image(
                    user_message=text_message or "Analyse cette image",
                    image_data=image_data
                )
            else:
                # Plusieurs images
                image_data_list = [img.read() for img in images]
                response_text = chatbot.chat_with_mixed_media(
                    user_message=text_message or "Analyse ces images",
                    images=image_data_list,
                    videos=None
                )
        
        # Cas 3: Texte + Vidéo(s)
        elif videos:
            logger.info(f"🎥 Mode: Texte + {len(videos)} vidéo(s)")
            
            # Traitement simple : prendre la première vidéo
            video_file = videos[0]
            video_path = video_file.temporary_file_path()
            processor = VideoProcessor(interval=5, max_frames=30)
            frames = processor.extract_frames(video_path)
            metadata = processor.get_video_metadata(video_path)
            
            # Analyser chaque frame avec ImageAnalyzer
            analyzer = ImageAnalyzer()
            frame_captions = []
            
            for i, frame_array in enumerate(frames):
                # Convertir numpy array en PIL Image
                frame_pil = Image.fromarray(frame_array)
                
                # Analyser le contenu du frame
                caption = analyzer.extract_image_content(frame_pil)
                frame_captions.append(caption)
                logger.info(f"Frame {i+1}/{len(frames)} analyzed")
    
            # Maintenant appeler le chatbot avec les vraies captions
            response_text = chatbot.chat_with_video(
                user_message=text_message or "Analyse cette vidéo",
                frame_captions=frame_captions,
                video_metadata=metadata
            )
        
        # Vérifier la réponse
        if not response_text:
            return JsonResponse({
                'error': 'Impossible de générer une réponse'
            }, status=500)
        
        logger.info(f"✅ Réponse générée: {len(response_text)} caractères")
        
        return JsonResponse({
            'success': True,
            'response': response_text,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du message: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


def chat_view(request):
    """Vue principale du chat"""
    return render(request, 'analyzer/chatbot.html')


def get_history(request):
    """Récupérer l'historique de conversation"""
    try:
        session_id = request.session.session_key
        
        if not session_id:
            return JsonResponse({'messages': []})
        
        chatbot = MultimodalChatbot(session_id=session_id)
        
        # Récupérer l'historique
        messages = chatbot.memory.messages
        
        return JsonResponse({
            'messages': messages,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur récupération historique: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def clear_history(request):
    """Effacer l'historique de conversation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        session_id = request.session.session_key
        
        if session_id:
            chatbot = MultimodalChatbot(session_id=session_id)
            chatbot.clear_history()
            logger.info(f"🗑️ Historique effacé pour session: {session_id}")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"❌ Erreur effacement historique: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def test_chatbot(request):
    """
    Vue de test pour vérifier que le chatbot fonctionne
    Accès: /test-chatbot/
    """
    try:
        # Test simple
        chatbot = MultimodalChatbot(session_id="test-session")
        response = chatbot.chat_text_only("Bonjour, test de connexion!")
        
        return JsonResponse({
            'success': True,
            'test_response': response,
            'message': '✅ Chatbot opérationnel'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '❌ Erreur de configuration'
        }, status=500)