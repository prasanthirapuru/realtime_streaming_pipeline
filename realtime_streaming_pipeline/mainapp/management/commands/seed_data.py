# mainapp/management/commands/seed_data.py
import os
import sys
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from mainapp.models import StreamData, LambdaInvocation
from userspp.models import UserProfile
import random
from datetime import datetime, timedelta
import json

class Command(BaseCommand):
    help = 'Seed the database with sample data for development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding database with sample data...'))
        
        # Create a test user if not exists
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            UserProfile.objects.create(user=test_user)
            self.stdout.write(self.style.SUCCESS('Created test user: testuser / testpass123'))
        
        # Clear existing data
        StreamData.objects.all().delete()
        LambdaInvocation.objects.all().delete()
        
        # Create sample stream data
        data_types = ['sensor', 'log', 'metric', 'event', 'custom']
        locations = ['server-room-1', 'server-room-2', 'office-floor', 'data-center', 'cloud-region']
        users = ['admin', 'sensor_01', 'system', 'monitor', 'tester']
        
        for i in range(25):
            data_type = random.choice(data_types)
            timestamp = datetime.now() - timedelta(hours=random.randint(1, 168))
            
            # Create different data content based on type
            if data_type == 'sensor':
                data_content = {
                    'data_type': 'sensor',
                    'sensor_id': f"sensor-{random.randint(100, 999)}",
                    'temperature': round(random.uniform(20.0, 35.0), 2),
                    'humidity': random.randint(30, 80),
                    'pressure': random.randint(1000, 1020),
                    'location': random.choice(locations),
                    'status': random.choice(['normal', 'warning', 'critical']),
                    'unit': '°C'
                }
            elif data_type == 'log':
                data_content = {
                    'data_type': 'log',
                    'level': random.choice(['INFO', 'WARNING', 'ERROR', 'DEBUG']),
                    'message': f"Log message {random.randint(1, 1000)}: System operation completed",
                    'component': random.choice(['auth', 'database', 'api', 'worker', 'scheduler']),
                    'timestamp': timestamp.isoformat()
                }
            elif data_type == 'metric':
                data_content = {
                    'data_type': 'metric',
                    'metric_name': random.choice(['cpu_usage', 'memory_usage', 'disk_io', 'network_latency']),
                    'value': round(random.uniform(0, 100), 2),
                    'unit': '%',
                    'threshold': 80,
                    'status': 'ok' if random.random() > 0.2 else 'exceeded'
                }
            elif data_type == 'event':
                data_content = {
                    'data_type': 'event',
                    'event_type': random.choice(['user_login', 'file_upload', 'data_processed', 'alert_triggered']),
                    'user': random.choice(users),
                    'details': f"Event occurred at {timestamp.strftime('%H:%M:%S')}",
                    'severity': random.choice(['low', 'medium', 'high'])
                }
            else:  # custom
                data_content = {
                    'data_type': 'custom',
                    'custom_field_1': f"value_{random.randint(1, 100)}",
                    'custom_field_2': random.choice(['active', 'inactive', 'pending']),
                    'custom_data': {
                        'score': random.randint(1, 100),
                        'category': random.choice(['A', 'B', 'C', 'D']),
                        'tags': ['tag1', 'tag2', 'tag3'][:random.randint(1, 3)]
                    }
                }
            
            stream = StreamData.objects.create(
                stream_id=f"STR-{random.randint(1000000000, 9999999999)}",
                partition_key=f"shard-{random.randint(1, 4)}",
                data_content=data_content,
                processed=random.choice([True, False]),
                lambda_invoked=random.choice([True, False]),
                timestamp=timestamp
            )
        
        # Create sample lambda invocations
        for i in range(10):
            invocation_time = datetime.now() - timedelta(hours=random.randint(1, 72))
            
            LambdaInvocation.objects.create(
                function_name='data-stream-processor',
                invocation_id=f"INV-{random.randint(10000, 99999)}",
                status=random.choice(['SUCCESS', 'FAILED']),
                input_data={
                    'batch_size': random.randint(1, 100),
                    'process_type': 'stream',
                    'timestamp': invocation_time.isoformat(),
                    'user': random.choice(users)
                },
                output_data={
                    'records_processed': random.randint(1, 50),
                    'processing_time_ms': random.randint(100, 2000),
                    'errors': random.randint(0, 3),
                    'status': 'completed'
                } if random.choice([True, False]) else None,
                timestamp=invocation_time
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {StreamData.objects.count()} stream records'))
        self.stdout.write(self.style.SUCCESS(f'Created {LambdaInvocation.objects.count()} lambda invocations'))
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
        
        # Display login info
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.WARNING("TEST CREDENTIALS:"))
        self.stdout.write("Username: testuser")
        self.stdout.write("Password: testpass123")
        self.stdout.write("="*50)