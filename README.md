# Student Admission App
> **AWS CDK** provisions infra → **GitHub Actions** builds & deploys → **Amazon EKS** runs the app

The Student Admission App is a web-based frontend application that allows prospective students to submit their admission applications for a certain college online. The form collects personal details, passport and visa information, contact details, academic history, English language proficiency results, and course selection preferences. It is built as a static frontend served via nginx, containerised with Docker, and deployed to Amazon EKS on AWS.

This project demonstrates modern DevOps practices — specifically how Infrastructure as Code (AWS CDK), containerisation (Docker), and a fully automated CI/CD pipeline (GitHub Actions) work together to deliver a reliable and repeatable deployment workflow. Rather than manually provisioning cloud resources or deploying by hand, every part of the stack — from the VPC and Kubernetes cluster down to the running application — is defined as code and automated.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  INFRA (one-time, via CDK)                      │
│                                                 │
│   CDK ──► CloudFormation ──► VPC                │
│                          ──► ECR Repository     │
│                          ──► EKS Cluster        │
│                          ──► Node Group         │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  CI/CD (every push to main, via GitHub Actions) │
│                                                 │
│   git push ──► Build Docker image               │
│            ──► Push to ECR                      │
│            ──► kubectl apply to EKS             │
│            ──► App live via LoadBalancer        │
└─────────────────────────────────────────────────┘
```

---

## Repo Structure

```
    student-admission-app/
    ├── app/
    │   ├── index.html              # Frontend (student admission form)
    │   ├── Dockerfile              # nginx container
    │   └── nginx.conf              # nginx config + /health endpoint
    │
    ├── infra/
    │   ├── cdk/                    # CDK — provisions AWS infrastructure
    │   │   ├── app.py              # CDK entry point
    │   │   ├── cdk.json            # CDK config
    │   │   ├── requirements.txt    # Python dependencies
    │   │   └── student_admission_app/
    │   │       └── stack.py        # VPC + ECR + EKS stack
    │   │
    │   └── k8s/                    # Kubernetes manifests
    │       ├── deployment.yaml     # 2 replicas + health checks
    │       └── service.yaml        # LoadBalancer service
    │
    ├── .github/workflows/
    │   └── deploy.yml              # CI/CD pipeline
    │
    └── README.md
```

---

## One-Time Infrastructure Setup (CDK)

```bash
cd infra/cdk

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/$CDK_DEFAULT_REGION

# Preview what will be created
cdk diff

# Deploy VPC + ECR + EKS
cdk deploy
```

CDK outputs after deploy:
```
Outputs:
StudentAdmissionAppStack.EcrRepositoryUri   = <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/student-admission-app
StudentAdmissionAppStack.EksClusterName     = student-admission-app-cluster
StudentAdmissionAppStack.EksClusterEndpoint = https://...
StudentAdmissionAppStack.VpcId              = vpc-xxxxxxxx
```

---

## GitHub Actions Setup

Add these secrets to your repo → **Settings → Secrets → Actions**:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret key |

Every push to `main` automatically:
1. Checks out code
2. Authenticates with AWS
3. Builds and pushes Docker image to ECR
4. Updates kubeconfig for EKS
5. Applies Kubernetes manifests
6. Prints the LoadBalancer URL

---

## Get the App URL

```bash
kubectl get service student-admission-app-service -w
```

Copy the `EXTERNAL-IP` hostname and open it in your browser.

---

## Tear Down

```bash
# Delete Kubernetes resources first
kubectl delete -f infra/k8s/

# Destroy CDK stack (deletes EKS, ECR, VPC)
cd infra/cdk
cdk destroy
```

---

## Updating the Frontend

To update the frontend, simply edit the `app/index.html` file and push to `main`:

```bash
git add app/index.html
git commit -m "update frontend"
git push origin main
```

GitHub Actions will automatically detect the push, build a new Docker image, push it to ECR, and apply a rolling update to EKS — no manual steps required. CDK only needs to be run again if the infrastructure itself changes (e.g. adding a new AWS resource). For all frontend changes, a git push is all it takes.

