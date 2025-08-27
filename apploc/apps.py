from django.apps import AppConfig

class ApplocConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apploc'

    def ready(self):
        import apploc.signals