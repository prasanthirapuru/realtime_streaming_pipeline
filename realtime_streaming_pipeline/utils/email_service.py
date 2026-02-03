# utils/email_service.py
import boto3
from django.conf import settings
from aws_config import AWSConfig

class EmailService:
    @staticmethod
    def send_stream_notification(recipient_email, stream_data):
        """Send notification when new data is streamed"""
        subject = "📊 New Data Streamed to Kinesis"
        
        # Prepare email body
        body_text = f"""
        New data has been streamed to AWS Kinesis
        
        Stream Details:
        - Stream ID: {stream_data.get('stream_id', 'N/A')}
        - Data Type: {stream_data.get('data_type', 'Unknown')}
        - Timestamp: {stream_data.get('timestamp', 'N/A')}
        - User: {stream_data.get('user', 'Unknown')}
        
        Data Content:
        {stream_data.get('data_content', 'No content')}
        
        ---
        This is an automated notification from Real-time Streaming Pipeline.
        """
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 15px 0; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 New Data Streamed</h1>
                    <p>Real-time Streaming Pipeline Notification</p>
                </div>
                
                <div class="content">
                    <p>New data has been successfully streamed to AWS Kinesis.</p>
                    
                    <div class="details">
                        <h3>Stream Details:</h3>
                        <ul>
                            <li><strong>Stream ID:</strong> {stream_data.get('stream_id', 'N/A')}</li>
                            <li><strong>Data Type:</strong> {stream_data.get('data_type', 'Unknown')}</li>
                            <li><strong>Timestamp:</strong> {stream_data.get('timestamp', 'N/A')}</li>
                            <li><strong>User:</strong> {stream_data.get('user', 'Unknown')}</li>
                        </ul>
                    </div>
                    
                    <div class="details">
                        <h3>Data Content:</h3>
                        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">
{stream_data.get('data_content', 'No content')}
                        </pre>
                    </div>
                    
                    <p>
                        <a href="http://localhost:8000/stream-data/" 
                           style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            View Stream Dashboard
                        </a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from Real-time Streaming Pipeline.</p>
                    <p>© 2024 Streaming Pipeline. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email using AWS SES
        return AWSConfig.send_email(recipient_email, subject, body_text, body_html)
    
    @staticmethod
    def send_lambda_invocation_notification(recipient_email, invocation_data):
        """Send notification when Lambda function is invoked"""
        subject = "⚡ Lambda Function Invoked"
        
        body_text = f"""
        AWS Lambda function has been invoked
        
        Invocation Details:
        - Function: {invocation_data.get('function_name', 'Unknown')}
        - Invocation ID: {invocation_data.get('invocation_id', 'N/A')}
        - Status: {invocation_data.get('status', 'Unknown')}
        - Timestamp: {invocation_data.get('timestamp', 'N/A')}
        - Invoked By: {invocation_data.get('invoked_by', 'Unknown')}
        
        ---
        This is an automated notification from Real-time Streaming Pipeline.
        """
        
        return AWSConfig.send_email(recipient_email, subject, body_text)
    
    @staticmethod
    def send_error_notification(recipient_email, error_data):
        """Send error notification"""
        subject = "🚨 Error in Streaming Pipeline"
        
        body_text = f"""
        An error occurred in the Real-time Streaming Pipeline
        
        Error Details:
        - Error Type: {error_data.get('error_type', 'Unknown')}
        - Error Message: {error_data.get('message', 'No details')}
        - Timestamp: {error_data.get('timestamp', 'N/A')}
        - Component: {error_data.get('component', 'Unknown')}
        
        Stack Trace:
        {error_data.get('stack_trace', 'No stack trace')}
        
        ---
        This is an automated error notification from Real-time Streaming Pipeline.
        """
        
        return AWSConfig.send_email(recipient_email, subject, body_text)
    
    @staticmethod
    def send_welcome_email(recipient_email, username):
        """Send welcome email to new users"""
        subject = "👋 Welcome to Real-time Streaming Pipeline"
        
        body_text = f"""
        Welcome to the Real-time Streaming Pipeline, {username}!
        
        Your account has been successfully created.
        
        Get started with:
        1. Login to your account
        2. Configure your AWS settings
        3. Start streaming data to Kinesis
        4. Monitor your streams in real-time
        
        Dashboard URL: http://localhost:8000/dashboard/
        
        ---
        Real-time Streaming Pipeline Team
        """
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 30px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .step {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👋 Welcome to Real-time Streaming Pipeline</h1>
                    <p>Hello, {username}!</p>
                </div>
                
                <div class="content">
                    <p>Your account has been successfully created and is ready to use.</p>
                    
                    <h3>Get Started:</h3>
                    
                    <div class="step">
                        <h4>1. Login to Your Account</h4>
                        <p>Use your credentials to access the dashboard.</p>
                    </div>
                    
                    <div class="step">
                        <h4>2. Configure AWS Settings</h4>
                        <p>Set up your AWS Kinesis and Lambda connections.</p>
                    </div>
                    
                    <div class="step">
                        <h4>3. Start Streaming Data</h4>
                        <p>Begin sending data to your Kinesis streams.</p>
                    </div>
                    
                    <div class="step">
                        <h4>4. Monitor in Real-time</h4>
                        <p>Watch your data flow through the pipeline.</p>
                    </div>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:8000/dashboard/" 
                           style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px;">
                            Go to Dashboard
                        </a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>Real-time Streaming Pipeline Team</p>
                    <p>© 2024 Streaming Pipeline. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return AWSConfig.send_email(recipient_email, subject, body_text, body_html)
    
    
    @staticmethod
    def send_upload_notification(recipient_email, upload_data):
        """Send notification when file is uploaded"""
        subject = "📁 File Uploaded Successfully"
        
        body_text = f"""
        File Upload Successful
        
        File Details:
        - File Name: {upload_data.get('file_name', 'N/A')}
        - Data Type: {upload_data.get('data_type', 'Unknown')}
        - File Size: {upload_data.get('file_size', '0')}
        - Upload Time: {upload_data.get('upload_time', 'N/A')}
        - Uploaded By: {upload_data.get('user', 'Unknown')}
        
        The file has been processed and is ready for streaming.
        
        ---
        This is an automated notification from Real-time Streaming Pipeline.
        """
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .file-info {{ background-color: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 15px 0; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                .file-icon {{ font-size: 48px; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="file-icon">📁</div>
                    <h1>File Upload Successful</h1>
                    <p>Your file has been uploaded and processed</p>
                </div>
                
                <div class="content">
                    <p>The following file has been successfully uploaded to the streaming pipeline:</p>
                    
                    <div class="file-info">
                        <h3>File Information:</h3>
                        <table style="width: 100%;">
                            <tr>
                                <td><strong>File Name:</strong></td>
                                <td>{upload_data.get('file_name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td><strong>Data Type:</strong></td>
                                <td>{upload_data.get('data_type', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td><strong>File Size:</strong></td>
                                <td>{upload_data.get('file_size', '0')}</td>
                            </tr>
                            <tr>
                                <td><strong>Upload Time:</strong></td>
                                <td>{upload_data.get('upload_time', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td><strong>Uploaded By:</strong></td>
                                <td>{upload_data.get('user', 'Unknown')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>The file is now available for streaming and processing through AWS Kinesis.</p>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:8000/user-upload/" 
                           style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px;">
                            View Upload History
                        </a>
                        <a href="http://localhost:8000/stream-data/" 
                           style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px; margin-left: 10px;">
                            View Stream Data
                        </a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from Real-time Streaming Pipeline.</p>
                    <p>© 2024 Streaming Pipeline. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return AWSConfig.send_email(recipient_email, subject, body_text, body_html)