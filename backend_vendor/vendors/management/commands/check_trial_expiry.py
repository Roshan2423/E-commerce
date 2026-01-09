"""
Management command to check trial expiry and send notifications.
Run this daily via cron: python manage.py check_trial_expiry
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from vendors.models import Business
from vendors.emails import send_trial_expiry_reminder, send_trial_expired_email


class Command(BaseCommand):
    help = 'Check trial expiry and send email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        self.stdout.write(self.style.NOTICE(f'Checking trial expiry at {now}'))

        # 1. Send reminders for trials expiring in 3 days
        self.send_expiry_reminders(now, dry_run)

        # 2. Expire and notify trials that have passed
        self.expire_trials(now, dry_run)

        self.stdout.write(self.style.SUCCESS('Trial check complete!'))

    def send_expiry_reminders(self, now, dry_run):
        """Send reminders for trials expiring in 3 days"""
        # Find businesses with trial expiring in 2-3 days (to catch them once)
        reminder_window_start = now + timedelta(days=2)
        reminder_window_end = now + timedelta(days=4)

        businesses = Business.objects.filter(
            subscription_status='trial',
            trial_end_date__gte=reminder_window_start,
            trial_end_date__lt=reminder_window_end,
        )

        self.stdout.write(f'Found {businesses.count()} businesses for expiry reminder')

        for business in businesses:
            if dry_run:
                self.stdout.write(
                    f'  [DRY RUN] Would send reminder to: {business.business_name} '
                    f'({business.owner.email if business.owner else "no email"})'
                )
            else:
                success = send_trial_expiry_reminder(business)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Sent reminder to: {business.business_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  Failed to send reminder to: {business.business_name}')
                    )

    def expire_trials(self, now, dry_run):
        """Expire trials and send notification"""
        # Find businesses with expired trials that haven't been notified
        businesses = Business.objects.filter(
            subscription_status='trial',
            trial_end_date__lt=now,
            trial_expiry_email_sent=False,
        )

        self.stdout.write(f'Found {businesses.count()} businesses with expired trials')

        for business in businesses:
            if dry_run:
                self.stdout.write(
                    f'  [DRY RUN] Would expire and notify: {business.business_name}'
                )
            else:
                # Mark as expired
                business.subscription_status = 'expired'
                business.save(update_fields=['subscription_status'])

                # Send notification
                success = send_trial_expired_email(business)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Expired and notified: {business.business_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Expired but failed to notify: {business.business_name}'
                        )
                    )
