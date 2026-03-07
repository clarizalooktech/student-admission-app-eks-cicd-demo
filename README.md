# EduApply — Student Admissions App
> Deployed on **Amazon EKS** via **GitHub Actions** CI/CD pipeline

---

## Repo Structure

```
eduapply/
├── app/
│   ├── index.html          # Frontend (single-page admission form)
│   ├── Dockerfile          # Containerises the app with nginx
│   └── nginx.conf          # Nginx config with /health endpoint
│
├── infra/
│   ├── k8s/
│   │   ├── deployment.yaml # Kubernetes Deployment (2 replicas)
│   │   └── service.yaml    # LoadBalancer Service
│   └── eks/
│       └── cluster.yaml    # eksctl cluster config
│
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline
│
└── README.md
```

---

## Prerequisites

| Tool | Purpose |
|---|---|
| AWS CLI | Authenticate with AWS |
| eksctl | Provision the EKS cluster |
| kubectl | Manage Kubernetes resources |
| Docker | Build container images locally (optional) |

---

## One-Time Setup

### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name eduapply --region ap-southeast-2
```

### 2. Provision EKS Cluster (~15 min)
```bash
eksctl create cluster -f infra/eks/cluster.yaml
```

### 3. Add GitHub Secrets
Go to your repo → **Settings → Secrets → Actions** and add:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret key |

> The IAM user needs: `AmazonEC2ContainerRegistryFullAccess` + `AmazonEKSClusterPolicy`

---

## Deploy

Every push to `main` automatically triggers the pipeline:

1. ✅ Checks out code
2. 🔐 Authenticates with AWS
3. 🐳 Builds and pushes Docker image to ECR
4. ☸️  Updates kubeconfig for EKS
5. 🚀 Applies Kubernetes manifests
6. 🌐 Prints the LoadBalancer URL

You can also trigger manually via **Actions → Run workflow**.

---

## Tear Down (after presentation)
```bash
# Delete EKS cluster — stops all billing
eksctl delete cluster --name eduapply-cluster --region ap-southeast-2
```

**Estimated cost for 24 hours: ~$5** ☕
