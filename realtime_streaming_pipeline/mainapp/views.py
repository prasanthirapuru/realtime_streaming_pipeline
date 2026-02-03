# mainapp/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import boto3
from aws_config import AWSConfig
from .models import StreamData, LambdaInvocation
from datetime import datetime  
from utils.email_service import EmailService
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def home(request):
    """
    Public home page that doesn't require login
    """
    if request.user.is_authenticated:
        # If user is already logged in, redirect to dashboard
        return redirect('dashboard')
    
    return render(request, 'mainapp/home.html')

@login_required
def dashboard(request):
    # Get statistics
    total_streams = StreamData.objects.count()
    processed_streams = StreamData.objects.filter(processed=True).count()
    lambda_invocations = LambdaInvocation.objects.count()
    
    context = {
        'total_streams': total_streams,
        'processed_streams': processed_streams,
        'lambda_invocations': lambda_invocations,
        'user': request.user,
        'development_mode': AWSConfig.DEVELOPMENT_MODE
    }
    return render(request, 'mainapp/dashboard.html', context)

@login_required
def stream_data_view(request):
    """View all stream data with pagination"""
    # Get all stream data ordered by timestamp
    streams = StreamData.objects.all().order_by('-timestamp')
    
    # Count statistics
    total_count = streams.count()
    processed_count = streams.filter(processed=True).count()
    pending_count = streams.filter(processed=False).count()
    
    # If no data exists in development mode, seed some
    if total_count == 0 and AWSConfig.DEVELOPMENT_MODE:
        self.stdout.write(self.style.WARNING("No data found. Seeding sample data..."))
        from django.core.management import call_command
        call_command('seed_data', '--quiet')
        streams = StreamData.objects.all().order_by('-timestamp')
        total_count = streams.count()
    
    # Add pagination (show 20 per page)
    page = request.GET.get('page', 1)
    paginator = Paginator(streams, 20)
    
    try:
        streams_page = paginator.page(page)
    except PageNotAnInteger:
        streams_page = paginator.page(1)
    except EmptyPage:
        streams_page = paginator.page(paginator.num_pages)
    
    return render(request, 'mainapp/stream_data.html', {
        'streams': streams_page,
        'total_count': total_count,
        'processed_count': processed_count,
        'pending_count': pending_count,
        'development_mode': AWSConfig.DEVELOPMENT_MODE,
        'page_obj': streams_page,
        'is_paginated': streams_page.has_other_pages()
    })

@login_required
def seed_sample_data(request):
    """View to seed sample data"""
    if request.method == 'POST':
        from django.core.management import call_command
        from django.contrib import messages
        
        try:
            call_command('seed_data', '--quiet')
            messages.success(request, 'Sample data seeded successfully!')
        except Exception as e:
            messages.error(request, f'Error seeding data: {str(e)}')
        
        return redirect('stream-data')
    
    return redirect('stream-data')

@login_required
def send_to_kinesis(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        kinesis_client = AWSConfig.get_kinesis_client()
        
        # Add metadata
        data['sender'] = request.user.username
        data['timestamp'] = datetime.now().isoformat()
        
        try:
            response = kinesis_client.put_record(
                StreamName=AWSConfig.KINESIS_STREAM_NAME,
                Data=json.dumps(data),
                PartitionKey=data.get('partition_key', 'default')
            )
            
            # Save to database
            StreamData.objects.create(
                stream_id=response['SequenceNumber'],
                partition_key=data.get('partition_key', 'default'),
                data_content=data,
                processed=False
            )
            
            return JsonResponse({
                'success': True,
                'sequence_number': response['SequenceNumber']
            })
        except Exception as e:
            # In development mode, create mock response
            if AWSConfig.DEVELOPMENT_MODE:
                import random
                mock_sequence = f"MOCK-{random.randint(1000000000000, 9999999999999)}"
                
                StreamData.objects.create(
                    stream_id=mock_sequence,
                    partition_key=data.get('partition_key', 'default'),
                    data_content=data,
                    processed=False
                )
                
                return JsonResponse({
                    'success': True,
                    'sequence_number': mock_sequence,
                    'mock': True
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def invoke_lambda(request):
    if request.method == 'POST':
        payload = {
            'action': 'process_stream',
            'timestamp': datetime.now().isoformat(),
            'invoked_by': request.user.username
        }
        
        try:
            lambda_client = AWSConfig.get_lambda_client()
            
            response = lambda_client.invoke(
                FunctionName=AWSConfig.LAMBDA_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Process response
            if 'Payload' in response:
                output = json.loads(response['Payload'].read())
            else:
                output = {'message': 'No payload returned'}
            
            # Save to database
            LambdaInvocation.objects.create(
                function_name=AWSConfig.LAMBDA_FUNCTION_NAME,
                invocation_id=response['ResponseMetadata']['RequestId'],
                status='SUCCESS' if response['StatusCode'] == 200 else 'FAILED',
                input_data=payload,
                output_data=output
            )
            
            # Send email notification
            try:
                invocation_data = {
                    'function_name': AWSConfig.LAMBDA_FUNCTION_NAME,
                    'invocation_id': response['ResponseMetadata']['RequestId'],
                    'status': 'SUCCESS' if response['StatusCode'] == 200 else 'FAILED',
                    'timestamp': datetime.now().isoformat(),
                    'invoked_by': request.user.username
                }
                
                email_result = EmailService.send_lambda_invocation_notification(
                    recipient_email=request.user.email if request.user.email else AWSConfig.SES_SENDER_EMAIL,
                    invocation_data=invocation_data
                )
            except Exception as e:
                print(f"Email error: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'invocation_id': response['ResponseMetadata']['RequestId'],
                'output': output
            })
            
        except Exception as e:
            # In development mode, create mock invocation
            if AWSConfig.DEVELOPMENT_MODE:
                import random
                mock_id = f"MOCK-INV-{random.randint(10000, 99999)}"
                
                LambdaInvocation.objects.create(
                    function_name=AWSConfig.LAMBDA_FUNCTION_NAME,
                    invocation_id=mock_id,
                    status='SUCCESS',
                    input_data=payload,
                    output_data={'message': 'Mock Lambda execution successful'}
                )
                
                return JsonResponse({
                    'success': True,
                    'invocation_id': mock_id,
                    'output': {'message': 'Mock Lambda execution successful'},
                    'mock': True
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def stream_status(request):
    """Check stream status - works with mock data in development"""
    
    stream_info = None
    error = None
    
    try:
        kinesis_client = AWSConfig.get_kinesis_client()
        
        # This will work in both development and production
        response = kinesis_client.describe_stream(
            StreamName=AWSConfig.KINESIS_STREAM_NAME
        )
        
        stream_info = {
            'name': response['StreamDescription']['StreamName'],
            'status': response['StreamDescription'].get('StreamStatus', 'ACTIVE'),
            'shards': len(response['StreamDescription'].get('Shards', [])),
            'arn': response['StreamDescription'].get('StreamARN', 'mock-arn'),
            'retention_hours': response['StreamDescription'].get('RetentionPeriodHours', 24)
        }
        
        # Add development mode flag
        stream_info['development_mode'] = AWSConfig.DEVELOPMENT_MODE
        
    except Exception as e:
        # In development mode, provide mock data
        if AWSConfig.DEVELOPMENT_MODE:
            stream_info = {
                'name': AWSConfig.KINESIS_STREAM_NAME,
                'status': 'ACTIVE',
                'shards': 2,
                'arn': 'arn:aws:kinesis:ap-south-1:123456789012:stream/realtime-data-stream',
                'retention_hours': 24,
                'development_mode': True
            }
        else:
            error = str(e)
    
    return render(request, 'mainapp/stream_status.html', {
        'stream_info': stream_info,
        'error': error
    })

@login_required
def data_visualization(request):
    return render(request, 'mainapp/data_visualization.html')

@login_required
def get_stream_detail(request, stream_id):
    """API endpoint to get stream data details"""
    try:
        stream = StreamData.objects.get(id=stream_id)
        return JsonResponse({
            'success': True,
            'data': stream.data_content
        })
    except StreamData.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Stream not found'
        })

@login_required
def process_stream(request, stream_id):
    """API endpoint to process a stream"""
    try:
        stream = StreamData.objects.get(id=stream_id)
        stream.processed = True
        stream.save()
        return JsonResponse({
            'success': True,
            'message': 'Stream processed successfully'
        })
    except StreamData.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Stream not found'
        })