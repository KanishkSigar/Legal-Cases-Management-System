"""Create (or update) the firm administrator account.

This is the only bootstrap the system needs: one admin who then creates
lawyers, clients, cases and appointments through the app. No demo data.

Usage:
    python manage.py createadmin                      # uses defaults / env vars
    python manage.py createadmin --username boss --password "S3cret!"

Environment variables (handy for deploys):
    ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update the firm administrator (superuser) account.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', 'admin'))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD'))
        parser.add_argument('--email', default=os.environ.get('ADMIN_EMAIL', 'admin@legalcms.local'))

    def handle(self, *args, **opts):
        username = opts['username']
        password = opts['password']
        email = opts['email']

        if not password:
            self.stderr.write(self.style.ERROR(
                'No password provided. Pass --password or set ADMIN_PASSWORD.'
            ))
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'role': User.Role.ADMIN},
        )
        user.email = email
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        verb = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} administrator "{username}". You can now sign in at the staff portal.'
        ))
