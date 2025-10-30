import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io
import re

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY not found!\n"
        "Please create a .env file with: GOOGLE_API_KEY=your_key_here"
    )

genai.configure(api_key=GOOGLE_API_KEY)
logger = logging.getLogger(__name__)


class ImageAnalyzer:
    
    def __init__(self, model_name='gemini-2.0-flash-exp'):
        self.model = genai.GenerativeModel(model_name)
    
    def extract_image_content(self, image_data):
        
        try:
            # Convertir en PIL Image
            image = self._load_image(image_data)
            
            # Prompt d'extraction précise
            extraction_prompt = """Analyse cette image et décris EXACTEMENT ce que tu vois.

RÈGLES STRICTES:
1. Si l'image contient du TEXTE (capture d'écran, document, test, article):
   → Transcris TOUT le texte, mot à mot, ligne par ligne
   → Préserve la structure et les titres
   
2. Si c'est une PHOTO/IMAGE sans texte:
   → Décris la scène, les objets, les personnes de manière factuelle
   
3. Si c'est un GRAPHIQUE/DIAGRAMME:
   → Explique sa structure et son contenu

NE FAIS AUCUNE INTERPRÉTATION CRÉATIVE. Sois FACTUEL."""
            
            response = self.model.generate_content([extraction_prompt, image])
            return response.text
            
        except Exception as e:
            logger.error(f"Image extraction error: {e}")
            return f"❌ Erreur d'extraction: {str(e)}"
    
    def _load_image(self, image_data):
        
        if isinstance(image_data, Image.Image):
            return image_data
        elif isinstance(image_data, bytes):
            return Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, str):  # Chemin de fichier
            return Image.open(image_data)
        else:
            raise ValueError(f"Format d'image non supporté: {type(image_data)}")



class PromptBuilder:
    
    
    @staticmethod
    def build_video_timeline(frame_captions, duration):
        
        if not frame_captions:
            return ""
        
        timeline = []
        frame_interval = duration / len(frame_captions) if len(frame_captions) > 0 else duration
        
        for i, caption in enumerate(frame_captions):
            timestamp = int(i * frame_interval)
            minutes, seconds = timestamp // 60, timestamp % 60
            timeline.append(f"[{minutes:02d}:{seconds:02d}] {caption}")
        
        return "\n".join(timeline)
    
    @staticmethod
    def build_video_analysis_prompt(user_message, frame_captions, video_metadata):
        
        duration = video_metadata.get('duration', 0)
        timeline = PromptBuilder.build_video_timeline(frame_captions, duration)
        
        return f"""Tu es un assistant sympathique qui analyse des vidéos. Réponds en FRANÇAIS de manière naturelle et conversationnelle.

L'utilisateur demande: "{user_message}"

Voici ce que j'ai vu dans la vidéo ({duration//60}min {duration%60}s):

{timeline}

COMMENT RÉPONDRE:
✅ Commence directement par répondre (ex: "Cette vidéo parle de...")
✅ Utilise des paragraphes courts et aérés
✅ Ajoute des émojis pour clarifier (📚 🎯 💡 🎥 ✨)
✅ Sois naturel, comme si tu parlais à un ami
✅ Mets en gras les points importants avec **texte**

❌ NE COMMENCE PAS par "Okay", "Absolutely", "Here's", "Let me"
❌ N'utilise PAS de titres anglais
❌ Ne fais PAS de liste numérotée rigide type "1. Type de contenu"

Réponds maintenant de façon claire et engageante en FRANÇAIS !"""

    @staticmethod
    def build_image_analysis_prompt(user_message, image_content):
        """Prompt d'analyse d'image conversationnel"""
        return f"""Tu es un assistant sympathique. L'utilisateur a partagé une image avec ce message: "{user_message}"

📸 CONTENU DE L'IMAGE:
{image_content}

COMMENT RÉPONDRE:
✅ Réponds en FRANÇAIS de manière naturelle
✅ Si c'est du texte: résume et commente le contenu
✅ Si c'est une photo: décris ce que tu vois
✅ Utilise des paragraphes courts et des émojis 📌 💡 ✨
✅ Sois direct et pertinent

❌ Ne commence PAS par "Okay", "Absolutely", "Here's"
❌ Pas de format trop structuré

Réponds naturellement !"""

    @staticmethod
    def build_text_only_prompt(user_message):
        """Prompt pour le chat texte simple"""
        return f"""Tu es un assistant sympathique et intelligent. Réponds en FRANÇAIS de manière naturelle.

Message de l'utilisateur: "{user_message}"

RÈGLES:
✅ Réponds de façon claire et conversationnelle
✅ Utilise des paragraphes courts
✅ Ajoute des émojis si ça aide (📌 💡 ✨ 🎯)
✅ Sois précis mais accessible

❌ Ne commence PAS par "Okay", "Absolutely", "Certainly"
❌ Évite le jargon inutile
❌ Pas de format trop formel

Réponds maintenant !"""

    @staticmethod
    def build_mixed_media_prompt(user_message, images=None, videos=None):
        """Prompt pour médias mixtes conversationnel"""
        context_parts = []
        
        if images:
            context_parts.append(f"📸 {len(images)} image(s) partagée(s):")
            for i, content in enumerate(images, 1):
                context_parts.append(f"\nImage {i}:")
                context_parts.append(f"{content[:300]}...")
        
        if videos:
            context_parts.append(f"\n🎥 {len(videos)} vidéo(s) partagée(s):")
            for i, video_data in enumerate(videos, 1):
                caps = video_data['captions']
                dur = video_data['metadata'].get('duration', 0)
                context_parts.append(f"\nVidéo {i} ({dur}s):")
                
                sample_size = min(3, len(caps))
                for j in range(sample_size):
                    context_parts.append(f"  → {caps[j][:80]}")
        
        return f"""Tu es un assistant sympathique. Réponds en FRANÇAIS de manière naturelle.

L'utilisateur demande: "{user_message}"

{chr(10).join(context_parts)}

COMMENT RÉPONDRE:
✅ Analyse ces médias de manière claire et naturelle
✅ Utilise des émojis et des paragraphes courts
✅ Sois direct et pertinent

❌ Pas de format trop formel
❌ Ne commence pas par "Okay" ou "Absolutely"

Réponds maintenant !"""



class ConversationMemory:
    
    
    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages
    
    def add_message(self, role, content):
        
        self.messages.append({"role": role, "content": content})
        
        if len(self.messages) > self.max_messages * 2:
            self.messages = self.messages[-self.max_messages * 2:]
    
    def get_history_context(self):
        
        if not self.messages:
            return ""
        
        history_lines = ["Historique récent:"]
        for msg in self.messages[-6:]:
            role = "User" if msg["role"] == "user" else "AI"
            content = msg["content"][:150]
            if len(msg["content"]) > 150:
                content += "..."
            history_lines.append(f"{role}: {content}")
        
        return "\n".join(history_lines) + "\n\n"
    
    def clear(self):
        
        self.messages = []



class MultimodalChatbot:
   
    def __init__(self, session_id):
        
        logger.info(f"Initializing chatbot for session: {session_id}")
        
        self.session_id = session_id
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.memory = ConversationMemory(max_messages=10)
        self.prompt_builder = PromptBuilder()
        self.image_analyzer = ImageAnalyzer()
        
        logger.info("Chatbot initialized successfully")
    
    def _clean_response(self, response_text):
        
        unwanted_patterns = [
            r'^(Okay|Absolutely|Certainly|Sure|Of course)[,!.\s]+',
            r'^(Here\'s|Here is|Let me|I\'ll)[,\s]+',
            r'^(D\'accord|Très bien|Bien sûr)[,!.\s]+'
        ]
        
        for pattern in unwanted_patterns:
            response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE)
        
        response_text = re.sub(r'\n{3,}', '\n\n', response_text)
        
        return response_text.strip()
    
    def _generate_response(self, prompt, include_history=True):
        
        try:
            if include_history:
                history_context = self.memory.get_history_context()
                full_prompt = f"{history_context}{prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            response_text = response.text
            
            # Nettoyer la réponse
            response_text = self._clean_response(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Désolé, une erreur s'est produite: {str(e)}"
    
    def chat_text_only(self, user_message):
        """Chat texte simple avec prompt amélioré"""
        logger.info(f"Processing text: {user_message[:50]}...")
        
        prompt = self.prompt_builder.build_text_only_prompt(user_message)
        
        response_text = self._generate_response(prompt)
        
        self.memory.add_message("user", user_message)
        self.memory.add_message("assistant", response_text)
        
        logger.info("Text response generated")
        return response_text
    
    def chat_with_image(self, user_message, image_data):
        
        logger.info("Processing image message (improved method)")
        
        try:
            
            image_content = self.image_analyzer.extract_image_content(image_data)
            logger.info(f"Image content extracted: {len(image_content)} chars")
            
            
            prompt = self.prompt_builder.build_image_analysis_prompt(
                user_message,
                image_content
            )
            
            
            response_text = self._generate_response(prompt)
            
            
            self.memory.add_message("user", f"[Image] {user_message}")
            self.memory.add_message("assistant", response_text)
            
            logger.info("Image response generated")
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat_with_image: {e}")
            return f"❌ Erreur lors de l'analyse de l'image: {str(e)}"
    
    def chat_with_image_direct(self, user_message, image_data):
        
        logger.info("Processing image message (direct method)")
        
        try:
            
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, str):
                image = Image.open(image_data)
            else:
                image = image_data
            
            
            history_context = self.memory.get_history_context()
            prompt = f"""{history_context}
L'utilisateur a partagé une image avec ce message: "{user_message}"

Analyse l'image et réponds en FRANÇAIS de manière naturelle:
- Si elle contient du TEXTE: lis-le attentivement
- Si c'est un test/article: identifie le sujet
- Réponds de manière précise et pertinente
- Utilise des émojis pour clarifier

❌ Ne commence PAS par "Okay", "Absolutely", "Here's" """
            
            
            response = self.model.generate_content([prompt, image])
            response_text = self._clean_response(response.text)
            
            self.memory.add_message("user", f"[Image] {user_message}")
            self.memory.add_message("assistant", response_text)
            
            logger.info("Direct image response generated")
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat_with_image_direct: {e}")
            return f"❌ Erreur: {str(e)}"
    
    def chat_with_video(self, user_message, frame_captions, video_metadata):
        
        logger.info(f"Processing video: {len(frame_captions)} frames")
        
        logger.info(f"First caption preview: {frame_captions[0][:100] if frame_captions else 'EMPTY'}")
        logger.info(f"Video metadata: {video_metadata}")
        
        prompt = self.prompt_builder.build_video_analysis_prompt(
            user_message,
            frame_captions,
            video_metadata
        )
        
        logger.info(f"Prompt preview: {prompt[:300]}...")
        
        response_text = self._generate_response(prompt, include_history=False)
        
        logger.info(f"Response preview: {response_text[:100]}...")
        
        duration = video_metadata.get('duration', 0)
        self.memory.add_message("user", f"[Video {duration}s] {user_message}")
        self.memory.add_message("assistant", response_text)
        
        logger.info("Video response generated")
        return response_text
    
    def chat_with_mixed_media(self, user_message, images=None, videos=None):
        """Chat avec médias mixtes"""
        logger.info("Processing mixed media")
        
        processed_images = []
        if images:
            for img_data in images:
                content = self.image_analyzer.extract_image_content(img_data)
                processed_images.append(content)
        
        prompt = self.prompt_builder.build_mixed_media_prompt(
            user_message,
            images=processed_images,
            videos=videos
        )
        
        response_text = self._generate_response(prompt, include_history=False)
        
        self.memory.add_message("user", f"[Mixed media] {user_message}")
        self.memory.add_message("assistant", response_text)
        
        logger.info("Mixed media response generated")
        return response_text
    
    def clear_history(self):
        """Effacer l'historique"""
        self.memory.clear()
        logger.info(f"History cleared for session {self.session_id}")