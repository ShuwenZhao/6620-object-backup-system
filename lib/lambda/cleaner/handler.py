import os
import boto3
import time
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize S3 and DynamoDB clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

BUCKET_DST = os.environ['BUCKET_DST']

def handler(event, context):
    # Run a loop to check every 5 seconds within the Lambda function
    for _ in range(12):  # 12 * 5 seconds = 60 seconds
        delete_disowned_objects()
        time.sleep(5)  # Sleep for 5 seconds between checks

def delete_disowned_objects():
    # Calculate threshold for disowned objects (10 seconds ago)
    threshold_time = int((datetime.utcnow() - timedelta(seconds=10)).timestamp())

    # Query for disowned objects in DynamoDB
    response = table.query(
        IndexName='statusIndex',
        KeyConditionExpression=(
            boto3.dynamodb.conditions.Key('status').eq('DISOWNED') &
            boto3.dynamodb.conditions.Key('disownedTimestamp').lt(threshold_time)
        )
    )

    # Delete each disowned copy from BucketDst and remove from Table T
    for item in response['Items']:
        copy_key = item['copyObjectKey']
        try:
            # Delete object from BucketDst
            s3.delete_object(Bucket=BUCKET_DST, Key=copy_key)
            # Delete entry from Table T
            table.delete_item(
                Key={'objectName': item['objectName'], 'timestamp': item['timestamp']}
            )
        except ClientError as e:
            print(f"Error deleting copy {copy_key} from {BUCKET_DST}: {e}")
