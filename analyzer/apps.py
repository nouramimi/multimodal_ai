from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)

class AnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analyzer'
    
    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('RUN_MAIN') is None:
            logger.info("=" * 60)
            logger.info("🚀 Initialisation de l'application Analyzer")
            logger.info("=" * 60)
            
            try:
                from .services.video_processor import VideoProcessor
                from .services.vision_model import VisionCaptioner
                from . import views
                
                logger.info("📥 Chargement du VideoProcessor...")
                # CHANGEMENT ICI : 10 secondes au lieu de 3
                views.video_processor = VideoProcessor(interval=10)
                logger.info("✅ VideoProcessor chargé (1 frame/10s)")
                
                logger.info("📥 Chargement du VisionCaptioner...")
                views.vision_captioner = VisionCaptioner()
                logger.info("✅ VisionCaptioner chargé!")
                
                logger.info("=" * 60)
                logger.info("🎉 Analyzer prêt!")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ ERREUR: {e}")
                import traceback
                logger.error(traceback.format_exc())