from django.apps import AppConfig
import threading
import logging

logger = logging.getLogger(__name__)

class BoothConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booth'

    def ready(self):
        # Import inside to avoid issues when Django loads models or migrations
        try:
            from .plc_oee import run  # Start the PLC monitoring system
            threading.Thread(target=run, daemon=True).start()
            logger.info("🚀 PLC OEE Monitoring thread started.")
        except Exception as e:
            logger.error(f"❌ Failed to start PLC monitoring thread: {e}")
