from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import UserUploadForm, UserProfileForm
from .models import UserProfile, DataUpload
from utils.email_service import EmailService  # Add this import
import json
import boto3
from datetime import datetime  # IMPORT THIS AT THE TOP!
from aws_config import AWSConfig

# Authentication Views
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful!')
            
            # Send welcome email
            try:
                email_result = EmailService.send_welcome_email(
                    recipient_email=user.email if user.email else AWSConfig.SES_SENDER_EMAIL,
                    username=user.username
                )
                if email_result['success']:
                    messages.info(request, 'Welcome email sent to your registered email!')
                else:
                    messages.warning(request, 'Welcome email could not be sent.')
            except Exception as e:
                print(f"Error sending welcome email: {str(e)}")
            
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# User Profile
@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user-profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'user/user-soft-myprofile.html', {
        'form': form,
        'profile': profile
    })

# User Submit Form - FIXED VERSION
@login_required
def user_submit_form(request):
    from datetime import datetime  # ADD THIS IMPORT INSIDE THE FUNCTION TOO
    
    if request.method == 'POST':
        # Process form data
        data_type = request.POST.get('data_type')
        data_content = request.POST.get('data_content')
        partition_key = request.POST.get('partition_key', str(request.user.id))
        
        # Parse JSON if provided as string
        try:
            if isinstance(data_content, str):
                parsed_content = json.loads(data_content)
            else:
                parsed_content = data_content
        except:
            parsed_content = data_content
        
        stream_data = {
            'user_id': request.user.id,
            'username': request.user.username,
            'data_type': data_type,
            'data_content': parsed_content,
            'timestamp': datetime.now().isoformat(),
            'partition_key': partition_key
        }
        
        try:
            # Send to Kinesis (or mock in development)
            kinesis_client = AWSConfig.get_kinesis_client()
            
            response = kinesis_client.put_record(
                StreamName=AWSConfig.KINESIS_STREAM_NAME,
                Data=json.dumps(stream_data),
                PartitionKey=partition_key
            )
            
            # Save stream data with sequence number
            from mainapp.models import StreamData
            StreamData.objects.create(
                stream_id=response['SequenceNumber'],
                partition_key=partition_key,
                data_content=stream_data,
                processed=False
            )
            
            # Send email notification
            try:
                from utils.email_service import EmailService
                email_result = EmailService.send_stream_notification(
                    recipient_email=request.user.email if request.user.email else AWSConfig.SES_SENDER_EMAIL,
                    stream_data=stream_data
                )
                
                if email_result['success']:
                    messages.info(request, f'Notification sent!')
            except Exception as e:
                print(f"Email notification error: {str(e)}")
            
            messages.success(request, f'✅ Data sent successfully! Sequence: {response["SequenceNumber"]}')
            
        except Exception as e:
            # In development mode, create mock data
            if AWSConfig.DEVELOPMENT_MODE:
                import random
                mock_sequence = f"MOCK-{random.randint(1000000000000, 9999999999999)}"
                
                from mainapp.models import StreamData
                StreamData.objects.create(
                    stream_id=mock_sequence,
                    partition_key=partition_key,
                    data_content=stream_data,
                    processed=False
                )
                
                messages.success(request, f'✅ [MOCK] Data saved locally! Mock Sequence: {mock_sequence}')
                messages.info(request, 'Running in development mode - using mock AWS services')
            else:
                messages.error(request, f'❌ Error: {str(e)}')
        
        return redirect('user-submit-form')
    
    # Add current timestamp for sample data
    current_timestamp = datetime.now().isoformat()
    
    return render(request, 'user/user-submit-form.html', {
        'current_timestamp': current_timestamp
    })

@login_required
def user_upload(request):
    """Handle file uploads with progress tracking"""
    from datetime import datetime
    import os
    
    if request.method == 'POST':
        form = UserUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                upload = form.save(commit=False)
                upload.user = request.user
                
                # Set file name from uploaded file
                if upload.file_path:
                    upload.file_name = upload.file_path.name
                
                # Save to database first
                upload.save()
                
                # Handle file processing based on development mode
                if not AWSConfig.DEVELOPMENT_MODE:
                    # Real AWS S3 upload
                    s3_client = AWSConfig.get_s3_client()
                    file = request.FILES['file_path']
                    
                    try:
                        # Upload to S3
                        s3_key = f'uploads/{request.user.id}/{datetime.now().strftime("%Y/%m/%d")}/{file.name}'
                        s3_client.upload_fileobj(
                            file,
                            AWSConfig.S3_BUCKET_NAME,
                            s3_key,
                            ExtraArgs={
                                'ContentType': file.content_type,
                                'Metadata': {
                                    'user': request.user.username,
                                    'data_type': upload.data_type,
                                    'upload_time': datetime.now().isoformat()
                                }
                            }
                        )
                        
                        # Update with S3 info
                        upload.kinesis_stream_id = f"s3://{AWSConfig.S3_BUCKET_NAME}/{s3_key}"
                        upload.save()
                        
                        messages.success(request, f'✅ File uploaded successfully to AWS S3!')
                        messages.info(request, f'File saved at: {upload.kinesis_stream_id}')
                        
                        # Send to Kinesis for processing
                        send_upload_to_kinesis(request, upload)
                        
                    except Exception as e:
                        messages.error(request, f'❌ Error uploading to S3: {str(e)}')
                        # Still save locally even if S3 fails
                        upload.save()
                
                else:
                    # Development mode - save locally and mock
                    upload.save()
                    
                    # Create local directory if it doesn't exist
                    media_path = upload.file_path.path
                    os.makedirs(os.path.dirname(media_path), exist_ok=True)
                    
                    messages.success(request, f'✅ File uploaded successfully (Development Mode)!')
                    messages.info(request, f'File saved locally at: {media_path}')
                    
                    # Mock Kinesis stream
                    send_upload_to_kinesis(request, upload)
                
                # Send email notification
                try:
                    from utils.email_service import EmailService
                    email_result = EmailService.send_upload_notification(
                        recipient_email=request.user.email if request.user.email else AWSConfig.SES_SENDER_EMAIL,
                        upload_data={
                            'file_name': upload.file_name,
                            'data_type': upload.data_type,
                            'file_size': upload.get_file_size_display(),
                            'upload_time': upload.upload_time.isoformat(),
                            'user': request.user.username
                        }
                    )
                    
                    if email_result['success']:
                        messages.info(request, '📧 Upload notification sent!')
                except Exception as e:
                    print(f"Email notification error: {str(e)}")
                
                return redirect('user-upload')
                
            except Exception as e:
                messages.error(request, f'❌ Error saving upload: {str(e)}')
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserUploadForm()
    
    # Get user's upload history
    upload_history = DataUpload.objects.filter(user=request.user).order_by('-upload_time')[:10]
    
    # Get upload statistics
    total_uploads = DataUpload.objects.filter(user=request.user).count()
    total_size = sum(upload.file_size for upload in DataUpload.objects.filter(user=request.user))
    
    return render(request, 'user/user-upload.html', {
        'form': form,
        'upload_history': upload_history,
        'total_uploads': total_uploads,
        'total_size': f"{total_size / (1024*1024):.2f} MB" if total_size > 0 else "0 MB",
        'development_mode': AWSConfig.DEVELOPMENT_MODE
    })

def send_upload_to_kinesis(request, upload):
    """Send upload metadata to Kinesis stream"""
    try:
        kinesis_client = AWSConfig.get_kinesis_client()
        
        stream_data = {
            'event_type': 'file_upload',
            'user_id': request.user.id,
            'username': request.user.username,
            'file_name': upload.file_name,
            'data_type': upload.data_type,
            'file_size': upload.file_size,
            'file_size_display': upload.get_file_size_display(),
            'upload_time': upload.upload_time.isoformat(),
            'file_extension': upload.get_file_extension(),
            'description': upload.description,
            'timestamp': datetime.now().isoformat()
        }
        
        if not AWSConfig.DEVELOPMENT_MODE:
            stream_data['s3_location'] = upload.kinesis_stream_id
        
        response = kinesis_client.put_record(
            StreamName=AWSConfig.KINESIS_STREAM_NAME,
            Data=json.dumps(stream_data),
            PartitionKey=str(request.user.id)
        )
        
        # Save stream ID
        upload.kinesis_stream_id = response['SequenceNumber']
        upload.save()
        
        print(f"[KINESIS] Upload metadata sent: {response['SequenceNumber']}")
        
    except Exception as e:
        print(f"[KINESIS ERROR] Failed to send upload metadata: {str(e)}")
        
        # In development mode, create mock response
        if AWSConfig.DEVELOPMENT_MODE:
            import random
            mock_sequence = f"UPLOAD-MOCK-{random.randint(1000000000000, 9999999999999)}"
            upload.kinesis_stream_id = mock_sequence
            upload.save()
            print(f"[MOCK KINESIS] Upload metadata saved with mock ID: {mock_sequence}")
            
            
# Test Email View
@login_required
def test_email(request):
    """Test email sending functionality"""
    from datetime import datetime  # ADD THIS IMPORT
    
    if request.method == 'POST':
        email_type = request.POST.get('email_type')
        recipient_email = request.POST.get('recipient_email', request.user.email)
        
        if not recipient_email:
            messages.error(request, 'Please provide a recipient email address')
            return redirect('test-email')
        
        try:
            if email_type == 'welcome':
                result = EmailService.send_welcome_email(
                    recipient_email=recipient_email,
                    username=request.user.username
                )
                message_type = 'Welcome'
                
            elif email_type == 'stream':
                result = EmailService.send_stream_notification(
                    recipient_email=recipient_email,
                    stream_data={
                        'stream_id': 'TEST-12345',
                        'data_type': 'Test Data',
                        'timestamp': datetime.now().isoformat(),
                        'user': request.user.username,
                        'data_content': {'test': 'This is a test notification'}
                    }
                )
                message_type = 'Stream Notification'
                
            elif email_type == 'lambda':
                result = EmailService.send_lambda_invocation_notification(
                    recipient_email=recipient_email,
                    invocation_data={
                        'function_name': 'test-function',
                        'invocation_id': 'TEST-INV-123',
                        'status': 'SUCCESS',
                        'timestamp': datetime.now().isoformat(),
                        'invoked_by': request.user.username
                    }
                )
                message_type = 'Lambda Notification'
                
            else:
                messages.error(request, 'Invalid email type selected')
                return redirect('test-email')
            
            if result['success']:
                messages.success(request, f'{message_type} email sent successfully to {recipient_email}')
            else:
                messages.error(request, f'Failed to send email: {result.get("error", "Unknown error")}')
                
        except Exception as e:
            messages.error(request, f'Error sending test email: {str(e)}')
        
        return redirect('test-email')
    
    return render(request, 'user/test_email.html')