# mainapp/management/commands/populate_sample_data.py
from django.core.management.base import BaseCommand
from mainapp.models import StreamData, LambdaInvocation
from datetime import datetime, timedelta
import random
import json

class Command(BaseCommand):
    help = 'Populate database with sample streaming data'
    
    def handle(self, *args, **options):
        # Clear existing data
        StreamData.objects.all().delete()
        LambdaInvocation.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create sample stream data
        sample_types = ['sensor', 'log', 'metric', 'event', 'custom']
        users = ['admin', 'sensor_01', 'system', 'monitor', 'tester']
        
        for i in range(20):
            data_type = random.choice(sample_types)
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))
            
            StreamData.objects.create(
                stream_id=f"STR-{random.randint(1000000000, 9999999999)}",
                partition_key=f"shard-{random.randint(1, 4)}",
                data_content={
                    'data_type': data_type,
                    'value': random.random() * 100,
                    'unit': '°C' if data_type == 'sensor' else '%',
                    'timestamp': timestamp.isoformat(),
                    'user': random.choice(users),
                    'location': f"location-{random.randint(1, 5)}",
                    'status': random.choice(['normal', 'warning', 'critical'])
                },
                processed=random.choice([True, False]),
                lambda_invoked=random.choice([True, False]),
                timestamp=timestamp
            )
        
        # Create sample lambda invocations
        for i in range(5):
            LambdaInvocation.objects.create(
                function_name='data-processor-lambda',
                invocation_id=f"INV-{random.randint(10000, 99999)}",
                status=random.choice(['SUCCESS', 'FAILED', 'IN_PROGRESS']),
                input_data={
                    'batch_size': random.randint(1, 100),
                    'process_type': 'batch',
                    'timestamp': datetime.now().isoformat()
                },
                output_data={
                    'records_processed': random.randint(1, 100),
                    'processing_time_ms': random.randint(100, 1000),
                    'status': 'completed'
                },
                timestamp=datetime.now() - timedelta(hours=random.randint(1, 24))
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {StreamData.objects.count()} stream records'))
        self.stdout.write(self.style.SUCCESS(f'Created {LambdaInvocation.objects.count()} lambda invocations'))
        
        # Show sample login info
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.WARNING("Sample User Credentials:"))
        self.stdout.write("Username: admin")
        self.stdout.write("Password: (use the one you created)")
        self.stdout.write("="*50)