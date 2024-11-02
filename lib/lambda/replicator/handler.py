import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize S3 and DynamoDB clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

BUCKET_SRC = os.environ['BUCKET_SRC']
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
        new_copy_key = f"{object_key}-{timestamp}"

        # Step 1: Copy the new object to BucketDst
        s3.copy_object(
            Bucket=BUCKET_DST,
            CopySource={'Bucket': BUCKET_SRC, 'Key': object_key},
            Key=new_copy_key
        )
        print(f"Copied {object_key} to {BUCKET_DST} as {new_copy_key}")

        # Step 2: Query Table T for an existing entry for this object
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('objectName').eq(object_key)
        )

        # Step 3: Delete all older copies in BucketDst and remove the old entries in Table T
        for item in response['Items']:
            old_copy_key = item['copyObjectKey']
            old_timestamp = item['timestamp']

            # Delete the old copy from BucketDst
            s3.delete_object(Bucket=BUCKET_DST, Key=old_copy_key)
            print(f"Deleted old copy: {old_copy_key} from {BUCKET_DST}")

            # Remove the old entry from Table T
            table.delete_item(
                Key={'objectName': object_key, 'timestamp': old_timestamp}
            )
            print(f"Deleted old entry in Table T for {object_key}")

        # Step 4: Add the new entry in Table T for the new copy
        table.put_item(
            Item={
                'objectName': object_key,
                'timestamp': timestamp,
                'copyObjectKey': new_copy_key,
                'status': 'ACTIVE',
            }
        )
        print(f"Added new copy to Table T for {object_key}")

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
