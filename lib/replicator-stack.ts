import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

interface ReplicatorStackProps extends cdk.StackProps {
  bucketSrc: s3.Bucket;
  bucketDst: s3.Bucket;
  tableT: dynamodb.Table;
}

export class ReplicatorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ReplicatorStackProps) {
    super(scope, id, props);

    const replicatorFn = new lambda.Function(this, 'ReplicatorFunction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'replicator.handler',
      code: lambda.Code.fromAsset('lambda/replicator'),
      environment: {
        BUCKET_SRC: props.bucketSrc.bucketName,
        BUCKET_DST: props.bucketDst.bucketName,
        TABLE_NAME: props.tableT.tableName,
      },
    });

    props.bucketSrc.addEventNotification(s3.EventType.OBJECT_CREATED_PUT, new s3n.LambdaDestination(replicatorFn));
    props.bucketSrc.addEventNotification(s3.EventType.OBJECT_REMOVED_DELETE, new s3n.LambdaDestination(replicatorFn));

    props.bucketDst.grantWrite(replicatorFn);
    props.tableT.grantReadWriteData(replicatorFn);
  }
}
