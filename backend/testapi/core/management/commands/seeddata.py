"""
Management command to seed the database with fake data
Usage: python manage.py seeddata [--users 50] [--posts 200]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from postapi.models import Post
from faker import Faker
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seeds the database with fake users and posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of fake users to create (default: 50)'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=200,
            help='Number of fake posts to create (default: 200)'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        num_posts = options['posts']

        self.stdout.write(self.style.WARNING('Starting database seeding...'))

        # Create special test users first
        self.stdout.write('Creating special test users...')
        test_users = self.create_test_users()

        # Create fake users
        self.stdout.write(f'Creating {num_users} fake users...')
        fake_users = self.create_fake_users(num_users)

        all_users = test_users + fake_users
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(all_users)} total users'))

        # Create fake posts
        self.stdout.write(f'Creating {num_posts} fake posts...')
        posts_created = self.create_fake_posts(all_users, num_posts)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {posts_created} posts'))

        self.stdout.write(self.style.SUCCESS('\n=== Seeding Complete ==='))
        self.stdout.write(self.style.SUCCESS('\nTest User Credentials:'))
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  Test User: username=testuser, password=test123')
        self.stdout.write('  John: username=john, password=john123')

    def create_test_users(self):
        """Create special test users that are always available"""
        test_users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_superuser': True,
                'is_staff': True,
                'bio': 'System administrator account for testing',
                'avatar': 'https://ui-avatars.com/api/?name=Admin+User&size=200&background=0D8ABC&color=fff'
            },
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'test123',
                'first_name': 'Test',
                'last_name': 'User',
                'is_superuser': False,
                'is_staff': False,
                'bio': 'Standard test user account',
                'avatar': 'https://ui-avatars.com/api/?name=Test+User&size=200&background=random'
            },
            {
                'username': 'john',
                'email': 'john@example.com',
                'password': 'john123',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_superuser': False,
                'is_staff': False,
                'bio': 'Another test user for demonstrations',
                'avatar': 'https://ui-avatars.com/api/?name=John+Doe&size=200&background=random'
            }
        ]

        created_users = []
        for user_data in test_users_data:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  ✓ Created test user: {user.username}')
            else:
                self.stdout.write(f'  - Test user already exists: {user.username}')
            created_users.append(user)

        return created_users

    def create_fake_users(self, count):
        """Create fake users with realistic data"""
        users = []
        
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 9999)}"
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='password123',  # Default password for all fake users
                first_name=first_name,
                last_name=last_name,
                bio=fake.text(max_nb_chars=200) if random.random() > 0.3 else '',
                avatar=f'https://ui-avatars.com/api/?name={first_name}+{last_name}&size=200&background=random'
            )
            users.append(user)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'  Created {i + 1}/{count} users...')

        return users

    def create_fake_posts(self, users, count):
        """Create fake posts distributed among users"""
        posts_created = 0
        
        for i in range(count):
            author = random.choice(users)
            title = fake.sentence(nb_words=random.randint(4, 10)).rstrip('.')
            
            # Generate unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Generate body with multiple paragraphs
            paragraphs = [fake.paragraph(nb_sentences=random.randint(3, 8)) 
                         for _ in range(random.randint(3, 10))]
            body = '\n\n'.join(paragraphs)
            
            # Random featured image from picsum
            image_id = random.randint(1, 1000)
            featured_image = f'https://picsum.photos/seed/{image_id}/800/600'
            
            Post.objects.create(
                author=author,
                title=title,
                slug=slug,
                body=body,
                excerpt=fake.text(max_nb_chars=250),
                featured_image=featured_image,
                is_published=random.random() > 0.1  # 90% published, 10% draft
            )
            
            posts_created += 1
            
            if (i + 1) % 50 == 0:
                self.stdout.write(f'  Created {i + 1}/{count} posts...')

        return posts_created