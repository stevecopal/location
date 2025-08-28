from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crée un superutilisateur'

    def handle(self, *args, **kwargs):
        username = 'admin'
        email = 'admin@admin.com'
        password = 'admin'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS('Superutilisateur créé avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Superutilisateur existe déjà'))