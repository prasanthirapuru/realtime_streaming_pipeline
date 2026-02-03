import json
import boto3
import time
from aws_config import AWSConfig

class KinesisDataProducer:
    def __init__(self):
        self.client = AWSConfig.get_kinesis_client()
        self.stream_name = AWSConfig.KINESIS_STREAM_NAME
    
    def send_to_stream(self, data, partition_key="default"):
        """
        Send data to Kinesis stream
        """
        try:
            response = self.client.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(data),
                PartitionKey=partition_key
            )
            print(f"Data sent to Kinesis. Sequence: {response['SequenceNumber']}")
            return response
        except Exception as e:
            print(f"Error sending to Kinesis: {e}")
            return None
    
    def send_batch(self, data_list, partition_key="default"):
        """
        Send batch data to Kinesis
        """
        records = []
        for data in data_list:
            record = {
                'Data': json.dumps(data),
                'PartitionKey': partition_key
            }
            records.append(record)
        
        try:
            response = self.client.put_records(
                Records=records,
                StreamName=self.stream_name
            )
            return response
        except Exception as e:
            print(f"Error sending batch to Kinesis: {e}")
            return None