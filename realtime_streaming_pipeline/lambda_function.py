import json
import boto3
import base64
from datetime import datetime

def lambda_handler(event, context):
    """
    AWS Lambda function to process Kinesis stream data
    """
    print(f"Lambda function invoked: {context.function_name}")
    
    processed_records = []
    
    for record in event['Records']:
        # Kinesis data is base64 encoded
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        data = json.loads(payload)
        
        # Process the data
        processed_data = process_stream_data(data)
        
        # Store in DynamoDB or send to another service
        store_processed_data(processed_data)
        
        processed_records.append({
            'record_id': record['kinesis']['sequenceNumber'],
            'processed_at': datetime.utcnow().isoformat(),
            'data': processed_data
        })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(processed_records)} records',
            'processed_records': processed_records
        })
    }

def process_stream_data(data):
    """
    Process incoming stream data
    """
    # Add processing logic here
    data['processed'] = True
    data['processing_timestamp'] = datetime.utcnow().isoformat()
    
    # Example: Detect anomalies or transform data
    if 'value' in data:
        if data['value'] > 100:
            data['alert'] = 'HIGH_VALUE_ALERT'
    
    return data

def store_processed_data(data):
    """
    Store processed data in DynamoDB
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('ProcessedStreamData')
    
    try:
        response = table.put_item(Item=data)
        return response
    except Exception as e:
        print(f"Error storing in DynamoDB: {e}")
        return None