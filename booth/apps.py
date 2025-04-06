from django.apps import AppConfig
import threading

class BoothConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booth'

    def ready(self):
        from .plc_oee import run  # Import only here to avoid Django setup conflicts
        threading.Thread(target=run, daemon=True).start()
