from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True)
    aws_user_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class DataUpload(models.Model):
    DATA_TYPE_CHOICES = [
        ('sensor', 'Sensor Data'),
        ('log', 'Log Files'),
        ('metric', 'Metrics'),
        ('event', 'Event Data'),
        ('custom', 'Custom Data'),
        ('csv', 'CSV File'),
        ('json', 'JSON File'),
        ('text', 'Text File'),
        ('image', 'Image File'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/%Y/%m/%d/')
    upload_time = models.DateTimeField(auto_now_add=True)
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES, default='custom')
    file_size = models.IntegerField(default=0)  # in bytes
    processed = models.BooleanField(default=False)
    kinesis_stream_id = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-upload_time']
    
    def __str__(self):
        return f"{self.file_name} - {self.user.username} ({self.data_type})"
    
    def save(self, *args, **kwargs):
        # Auto-set file size if file exists
        if self.file_path and hasattr(self.file_path, 'size'):
            self.file_size = self.file_path.size
        
        # Auto-set file name from file if not provided
        if not self.file_name and self.file_path:
            self.file_name = self.file_path.name
        
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Return human readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def get_file_extension(self):
        """Get file extension"""
        if self.file_path:
            return self.file_path.name.split('.')[-1].lower()
        return ''