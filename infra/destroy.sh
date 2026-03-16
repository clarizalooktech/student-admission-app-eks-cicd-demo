#!/bin/bash
echo "Cleaning up Kubernetes resources before CDK destroy..."

# Delete all services and ingresses (this removes ELBs)
kubectl delete svc --all -n default
kubectl delete ingress --all -n default

echo "Waiting 60 seconds for ELBs to drain..."
sleep 60

# Verify ELBs are gone
echo "Checking for remaining ELBs..."
# Find the NLB
aws elbv2 describe-load-balancers --region ap-southeast-2 \
  --query 'LoadBalancers[*].[LoadBalancerName,LoadBalancerArn]' \
  --output table

# Delete it
aws elbv2 delete-load-balancer \
  --load-balancer-arn <arn-from-above> \
  --region ap-southeast-2

echo "Running cdk destroy..."
cdk destroy --force