import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';

interface CleanerStackProps extends cdk.StackProps {
    bucketDst: s3.Bucket;
    tableT: dynamodb.Table;
}

export class CleanerStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: CleanerStackProps) {
        super(scope, id, props);

        const cleanerFn = new lambda.Function(this, 'CleanerFunction', {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'handler.handler',
            code: lambda.Code.fromAsset('lib/lambda/cleaner'),
            environment: {
                BUCKET_DST: props.bucketDst.bucketName,
                TABLE_NAME: props.tableT.tableName,
            },
        });

        const rule = new events.Rule(this, 'CleanerSchedule', {
            schedule: events.Schedule.rate(cdk.Duration.minutes(1)),
        });
        rule.addTarget(new targets.LambdaFunction(cleanerFn));

        // Grant permissions without direct dependency
        cleanerFn.addToRolePolicy(new iam.PolicyStatement({
            actions: ['s3:DeleteObject'],
            resources: [`arn:aws:s3:::${props.bucketDst.bucketName}/*`],
        }));

        props.tableT.grantReadWriteData(cleanerFn);
    }
}
