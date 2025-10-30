from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)

class AnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analyzer'
    
    def ready(self):
        """Lightweight initialization - no heavy models"""
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('RUN_MAIN') is None:
            logger.info("=" * 60)
            logger.info("🚀 Application Analyzer initialisée")
            logger.info("✅ Utilisation de Gemini API (pas de modèles locaux)")
            logger.info("=" * 60)