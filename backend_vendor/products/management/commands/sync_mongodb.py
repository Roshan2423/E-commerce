"""
Django Management Command: sync_mongodb
Syncs all Django data to MongoDB

Usage:
    python manage.py sync_mongodb
"""

from django.core.management.base import BaseCommand
from ecommerce.mongodb_sync import full_sync


class Command(BaseCommand):
    help = 'Sync all Django data to MongoDB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting MongoDB sync...'))
        full_sync()
        self.stdout.write(self.style.SUCCESS('MongoDB sync completed!'))
