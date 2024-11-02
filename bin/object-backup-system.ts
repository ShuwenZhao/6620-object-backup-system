#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { StorageStack1 } from '../lib/storage-stack';
import { ReplicatorStack } from '../lib/replicator-stack';
import { CleanerStack } from '../lib/cleaner-stack';

const app = new cdk.App();

const storageStack = new StorageStack1(app, 'StorageStack1');
new ReplicatorStack(app, 'ReplicatorStack', {
  bucketSrc: storageStack.bucketSrc,
  bucketDst: storageStack.bucketDst,
  tableT: storageStack.tableT,
});
new CleanerStack(app, 'CleanerStack', {
  bucketDst: storageStack.bucketDst,
  tableT: storageStack.tableT,
});
