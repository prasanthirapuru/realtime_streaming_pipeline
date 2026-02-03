from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Import views from apps
from userspp.views import (
    test_email, user_profile, user_submit_form, user_upload, 
    register_view, logout_view
)
from mainapp.views import (
    process_stream, get_stream_detail, home, dashboard, stream_data_view, send_to_kinesis,
    invoke_lambda, stream_status, data_visualization, seed_sample_data
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('test-email/',test_email, name='test-email'),
    # Public Home Page (NO login required)
    path('', home, name='home'),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True  # Redirect if already logged in
    ), name='login'),
    
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/register/', register_view, name='register'),
    
    # User URLs (require login)
    path('user-profile/', user_profile, name='user-profile'),
    path('user-submit-form/', user_submit_form, name='user-submit-form'),
    path('user-upload/', user_upload, name='user-upload'),
    
    # Main App URLs (require login)
    
    path('seed-sample-data/', seed_sample_data, name='seed-sample-data'),
    path('dashboard/', dashboard, name='dashboard'),
    path('stream-data/', stream_data_view, name='stream-data'),
    path('send-to-kinesis/', send_to_kinesis, name='send-to-kinesis'),
    path('invoke-lambda/', invoke_lambda, name='invoke-lambda'),
    path('stream-status/', stream_status, name='stream-status'),
    path('data-visualization/', data_visualization, name='data-visualization'),
    path('api/get-stream-detail/<int:stream_id>/',get_stream_detail, name='api-get-stream-detail'),
    path('api/process-stream/<int:stream_id>/',process_stream, name='api-process-stream'),
    
    # API Endpoints
    path('api/send-stream/', send_to_kinesis, name='api-send-stream'),
    path('api/get-stream-data/', stream_data_view, name='api-get-stream-data'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)