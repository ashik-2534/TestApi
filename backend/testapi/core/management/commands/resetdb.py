"""
Management command to reset the database
Usage: python manage.py resetdb [--no-seed]
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
import time

LOCK_FILE = '/tmp/reset_in_progress'


class Command(BaseCommand):
    help = 'Flushes database, runs migrations, and loads seed data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-seed',
            action='store_true',
            help='Skip seeding data after reset'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to seed (default: 50)'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=200,
            help='Number of posts to seed (default: 200)'
        )

    def handle(self, *args, **options):
        # Create lock file to trigger maintenance mode
        self.stdout.write(self.style.WARNING('=== Starting Database Reset ==='))
        
        try:
            # Step 1: Create maintenance lock
            self.stdout.write('Creating maintenance lock...')
            with open(LOCK_FILE, 'w') as f:
                f.write(str(time.time()))
            self.stdout.write(self.style.SUCCESS('✓ Maintenance mode activated'))

            # Step 2: Flush database
            self.stdout.write('\nFlushing database...')
            call_command('flush', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Database flushed'))

            # Step 3: Run migrations
            self.stdout.write('\nRunning migrations...')
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Migrations applied'))

            # Step 4: Create cache table (if using database cache)
            try:
                self.stdout.write('\nCreating cache table...')
                call_command('createcachetable', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✓ Cache table created'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Cache table creation skipped: {e}'))

            # Step 5: Reset media directory
            self.stdout.write('\nResetting media directory...')
            media_root = settings.MEDIA_ROOT
            if os.path.exists(media_root):
                shutil.rmtree(media_root)
                self.stdout.write(f'  Removed old media directory')
            os.makedirs(media_root, exist_ok=True)
            self.stdout.write(self.style.SUCCESS('✓ Media directory reset'))

            # Step 6: Seed data (unless --no-seed flag is used)
            if not options['no_seed']:
                self.stdout.write('\nSeeding database...')
                call_command(
                    'seeddata',
                    users=options['users'],
                    posts=options['posts'],
                    verbosity=1
                )
            else:
                self.stdout.write(self.style.WARNING('Skipping data seeding (--no-seed flag)'))

            self.stdout.write(self.style.SUCCESS('\n=== Database Reset Complete ==='))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error during reset: {str(e)}'))
            raise
        
        finally:
            # Always remove lock file
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
                self.stdout.write(self.style.SUCCESS('✓ Maintenance mode deactivated'))
                self.stdout.write(self.style.SUCCESS('\nService is now available!'))