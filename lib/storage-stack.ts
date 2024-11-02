import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class StorageStack1 extends cdk.Stack {
  public readonly bucketSrc: s3.Bucket;
  public readonly bucketDst: s3.Bucket;
  public readonly tableT: dynamodb.Table;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.bucketSrc = new s3.Bucket(this, 'BucketSrc');
    this.bucketDst = new s3.Bucket(this, 'BucketDst');

    this.tableT = new dynamodb.Table(this, 'TableT', {
      partitionKey: { name: 'objectName', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.NUMBER },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    this.tableT.addGlobalSecondaryIndex({
      indexName: 'statusIndex',
      partitionKey: { name: 'status', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'disownedTimestamp', type: dynamodb.AttributeType.NUMBER },
    });
  }
}
