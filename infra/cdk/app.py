#!/usr/bin/env python3
import os
import aws_cdk as cdk
from student_admission_app.stack import StudentAdmissionAppStack

app = cdk.App()

StudentAdmissionAppStack(
    app,
    "StudentAdmissionAppStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-2")
    ),
    description="Student Admission App — VPC, EKS, and ECR infrastructure"
)

app.synth()
