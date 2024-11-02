import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

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
            handler: 'handler.handler',
            code: lambda.Code.fromAsset('lib/lambda/replicator'),
            environment: {
                BUCKET_SRC: props.bucketSrc.bucketName,
                BUCKET_DST: props.bucketDst.bucketName,
                TABLE_NAME: props.tableT.tableName,
            },
        });

        // Grant permissions without creating a dependency
        replicatorFn.addToRolePolicy(new iam.PolicyStatement({
            actions: ['s3:GetObject', 's3:PutObject', 's3:DeleteObject'],
            resources: [
                `arn:aws:s3:::${props.bucketSrc.bucketName}/*`,
                `arn:aws:s3:::${props.bucketDst.bucketName}/*`
            ],
        }));

        // Grant DynamoDB permissions for put and update actions
        replicatorFn.addToRolePolicy(new iam.PolicyStatement({
            actions: ['dynamodb:PutItem', 'dynamodb:UpdateItem', 'dynamodb:Query', 'dynamodb:DeleteItem'],
            resources: [props.tableT.tableArn],
        }));
    }
}
