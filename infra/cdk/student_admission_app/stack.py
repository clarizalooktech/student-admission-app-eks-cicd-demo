import os
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_eks as eks,
    aws_iam as iam,
)
from constructs import Construct


class StudentAdmissionAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── 1. VPC
        # 2 AZs, public + private subnets, NAT Gateway for private subnets
        vpc = ec2.Vpc(
            self, "StudentAdmissionVpc",
            vpc_name="student-admission-app-vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # ── 2. ECR Repository
        repository = ecr.Repository(
            self, "StudentAdmissionEcr",
            repository_name="student-admission-app",
            removal_policy=RemovalPolicy.DESTROY,       # safe to delete on cdk destroy
            empty_on_delete=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                )
            ],
        )

        # ── 3. IAM Role for EKS cluster
        eks_role = iam.Role(
            self, "EksClusterRole",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"),
            ],
        )

        # ── 4. EKS Cluster
        cluster = eks.Cluster(
            self, "StudentAdmissionCluster",
            cluster_name="student-admission-app-cluster",
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            default_capacity=0,         # we define node group below
            version=eks.KubernetesVersion.V1_29,
            role=eks_role,
        )

        # ── 5. Managed Node Group
        cluster.add_nodegroup_capacity(
            "StudentAdmissionNodes",
            nodegroup_name="student-admission-app-nodes",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=1,
            max_size=3,
            desired_size=2,
            ami_type=eks.NodegroupAmiType.AL2_X86_64,
        )

        # ── 6. IAM Service Account for AWS Load Balancer Controller
        alb_service_account = cluster.add_service_account(
            "ALBServiceAccount",
            name="aws-load-balancer-controller",
            namespace="kube-system",
        )

        # Attach required IAM policies for the Load Balancer Controller
        alb_service_account.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "ElasticLoadBalancingFullAccess"
            )
        )

        # Additional inline policy for EC2/EKS permissions the controller needs
        alb_service_account.add_to_principal_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:DescribeAccountAttributes",
                    "ec2:DescribeAddresses",
                    "ec2:DescribeAvailabilityZones",
                    "ec2:DescribeInternetGateways",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeVpcPeeringConnections",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeInstances",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DescribeTags",
                    "ec2:GetCoipPoolUsage",
                    "ec2:DescribeCoipPools",
                    "ec2:CreateSecurityGroup",
                    "ec2:CreateTags",
                    "ec2:DeleteTags",
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress",
                    "ec2:DeleteSecurityGroup",
                    "elasticloadbalancing:*",
                ],
                resources=["*"],
            )
        )

        # ── 7. Install AWS Load Balancer Controller via Helm
        alb_chart = cluster.add_helm_chart(
            "AWSLoadBalancerController",
            chart="aws-load-balancer-controller",
            repository="https://aws.github.io/eks-charts",
            namespace="kube-system",
            values={
                "clusterName": cluster.cluster_name,
                "serviceAccount": {
                    "create": False,
                    "name": "aws-load-balancer-controller",
                },
            },
        )

        # Helm chart must wait for the service account to be ready
        alb_chart.node.add_dependency(alb_service_account)

        # ── 8. Allow GitHub Actions IAM user to push to ECR + access EKS
        github_actions_user = iam.User.from_user_name(
            self, "GithubActionsUser", os.environ.get("AWS_IAM_USER", "clarilook.aws")
        )
        repository.grant_push(github_actions_user)
        cluster.aws_auth.add_user_mapping(
            github_actions_user,
            groups=["system:masters"],
        )

        # ── 9. Outputs
        CfnOutput(self, "VpcId",
            value=vpc.vpc_id,
            description="VPC ID"
        )
        CfnOutput(self, "EcrRepositoryUri",
            value=repository.repository_uri,
            description="ECR Repository URI — use this in GitHub Actions"
        )
        CfnOutput(self, "EksClusterName",
            value=cluster.cluster_name,
            description="EKS Cluster Name"
        )
        CfnOutput(self, "EksClusterEndpoint",
            value=cluster.cluster_endpoint,
            description="EKS Cluster Endpoint"
        )