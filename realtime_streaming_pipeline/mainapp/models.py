from django.db import models

class StreamData(models.Model):
    stream_id = models.CharField(max_length=100, unique=True)
    partition_key = models.CharField(max_length=100)
    data_content = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    lambda_invoked = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Stream {self.stream_id}"

class LambdaInvocation(models.Model):
    function_name = models.CharField(max_length=100)
    invocation_id = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    input_data = models.JSONField(null=True, blank=True)
    output_data = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.function_name} - {self.status}"