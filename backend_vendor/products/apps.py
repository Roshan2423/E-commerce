from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        """Connect MongoDB sync signals when app is ready"""
        try:
            from ecommerce.signals import connect_signals
            connect_signals()
        except Exception as e:
            print(f"[MongoDB Sync] Failed to connect signals: {e}")