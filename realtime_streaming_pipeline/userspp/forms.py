from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, DataUpload

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'profile_image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your address'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserUploadForm(forms.ModelForm):
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe what this file contains...'
        }),
        label='Description (Optional)'
    )
    
    class Meta:
        model = DataUpload
        fields = ['file_path', 'data_type', 'description']
        widgets = {
            'file_path': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv,.json,.txt,.log,.xlsx,.xls,.pdf,.jpg,.jpeg,.png,.parquet'
            }),
            'data_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'file_path': 'Select File',
            'data_type': 'Data Type',
        }
    
    def clean_file_path(self):
        file = self.cleaned_data.get('file_path')
        if file:
            # Validate file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError(f'File size must be under 10MB. Current size: {file.size / (1024*1024):.2f}MB')
            
            # Validate file extension
            allowed_extensions = ['.csv', '.json', '.txt', '.log', '.xlsx', '.xls', '.pdf', '.jpg', '.jpeg', '.png', '.parquet']
            extension = file.name.split('.')[-1].lower()
            if f'.{extension}' not in allowed_extensions:
                raise forms.ValidationError(f'File type .{extension} not allowed. Allowed types: {", ".join([ext[1:] for ext in allowed_extensions])}')
        
        return file