import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize S3 and DynamoDB clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

BUCKET_DST = os.environ['BUCKET_DST']

def handler(event, context):
    for record in event['Records']:
        event_name = record['eventName']
        object_key = record['s3']['object']['key']

        if "ObjectCreated:Put" in event_name:
            handle_put_event(object_key)
        elif "ObjectRemoved:Delete" in event_name:
            handle_delete_event(object_key)

def handle_put_event(object_key):
    try:
        # Generate a unique name for the copy with a timestamp
        timestamp = int(datetime.utcnow().timestamp())
        copy_key = f"{object_key}-{timestamp}"

        # Copy the object to BucketDst
        s3.copy_object(
            Bucket=BUCKET_DST,
            CopySource={'Bucket': os.environ['BUCKET_SRC'], 'Key': object_key},
            Key=copy_key
        )

        # Fetch existing copies in Table T and delete the oldest if more than one exists
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('objectName').eq(object_key)
        )

        if response['Items']:
            # Sort items by timestamp to find the oldest
            sorted_items = sorted(response['Items'], key=lambda x: x['timestamp'])
            if len(sorted_items) > 1:
                oldest_copy_key = sorted_items[0]['copyObjectKey']
                # Delete the oldest copy from BucketDst
                s3.delete_object(Bucket=BUCKET_DST, Key=oldest_copy_key)
                # Remove the oldest entry from Table T
                table.delete_item(
                    Key={'objectName': object_key, 'timestamp': sorted_items[0]['timestamp']}
                )

        # Update Table T with the new copy details
        table.put_item(
            Item={
                'objectName': object_key,
                'timestamp': timestamp,
                'copyObjectKey': copy_key,
                'status': 'ACTIVE',
            }
        )
    except ClientError as e:
        print(f"Error handling PUT event for {object_key}: {e}")

def handle_delete_event(object_key):
    try:
        # Mark items in Table T as 'DISOWNED' when original object is deleted
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('objectName').eq(object_key)
        )

        for item in response['Items']:
            table.update_item(
                Key={'objectName': object_key, 'timestamp': item['timestamp']},
                UpdateExpression="SET #s = :s, disownedTimestamp = :dt",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':s': 'DISOWNED',
                    ':dt': int(datetime.utcnow().timestamp())
                }
            )
    except ClientError as e:
        print(f"Error handling DELETE event for {object_key}: {e}")
