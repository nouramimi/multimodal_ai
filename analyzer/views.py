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

from .services.chatbot_orchestrator import MultimodalChatbot

logger = logging.getLogger(__name__)

_video_processor = None

def get_video_processor():
    
    global _video_processor
    if _video_processor is None:
        from .services.video_processor import VideoProcessor
        _video_processor = VideoProcessor(interval=10, max_frames=30)
        logger.info("📥 VideoProcessor chargé")
    return _video_processor


@csrf_exempt
def send_message(request):
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        text_message = request.POST.get('message', '').strip()
        images = request.FILES.getlist('images')
        videos = request.FILES.getlist('videos')
        session_id = request.session.session_key
        
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        logger.info(f"📨 Traitement du message: texte={bool(text_message)}, "
                   f"images={len(images)}, vidéos={len(videos)}")
        
        if not text_message and not images and not videos:
            return JsonResponse({
                'error': 'Message vide. Envoyez du texte, une image ou une vidéo.'
            }, status=400)
        
        chatbot = MultimodalChatbot(session_id=session_id)
        
        response_text = None
        
        if text_message and not images and not videos:
            logger.info("💬 Mode: Texte seul")
            response_text = chatbot.chat_text_only(text_message)
        
        elif images:
            logger.info(f"🖼️ Mode: Texte + {len(images)} image(s)")
            
            if len(images) == 1:
                
                image_data = images[0].read()
                response_text = chatbot.chat_with_image(
                    user_message=text_message or "Analyse cette image",
                    image_data=image_data
                )
            else:
                
                image_data_list = [img.read() for img in images]
                response_text = chatbot.chat_with_mixed_media(
                    user_message=text_message or "Analyse ces images",
                    images=image_data_list,
                    videos=None
                )
        
        elif videos:
            logger.info(f"🎥 Mode: Texte + {len(videos)} vidéo(s)")
            
            video_file = videos[0]
            video_path = video_file.temporary_file_path()
            processor = get_video_processor() 
            frames = processor.extract_frames(video_path)
            metadata = processor.get_video_metadata(video_path)
            
            analyzer = ImageAnalyzer()
            frame_captions = []
            
            for i, frame_array in enumerate(frames):
                
                frame_pil = Image.fromarray(frame_array)
                
                
                caption = analyzer.extract_image_content(frame_pil)
                frame_captions.append(caption)
                logger.info(f"Frame {i+1}/{len(frames)} analyzed")
    
            
            response_text = chatbot.chat_with_video(
                user_message=text_message or "Analyse cette vidéo",
                frame_captions=frame_captions,
                video_metadata=metadata
            )
        
        
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
    
    return render(request, 'analyzer/chatbot.html')


def get_history(request):
    
    try:
        session_id = request.session.session_key
        
        if not session_id:
            return JsonResponse({'messages': []})
        
        chatbot = MultimodalChatbot(session_id=session_id)
        
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
    
    try:
        
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