# AWS Deployment Guide

This guide covers deploying the Alert Dashboard to AWS using different approaches.

## Deployment Options

| Option | Complexity | Cost | Best For |
|--------|------------|------|----------|
| EC2 + Docker | Low | $ | Small teams, simple setup |
| ECS Fargate | Medium | $$ | Production, auto-scaling |
| EKS | High | $$$ | Enterprise, Kubernetes experience |

---

## Option 1: EC2 + Docker Compose (Recommended for Starting)

This is the simplest approach, similar to the VirtualBox setup.

### Prerequisites

- AWS Account
- AWS CLI configured locally
- Basic knowledge of EC2

### Step 1: Launch EC2 Instance

1. **Go to EC2 Dashboard** → Launch Instance

2. **Configure Instance**:
   - **Name**: `alert-dashboard`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: `t3.small` (minimum) or `t3.medium` (recommended)
   - **Key pair**: Create or select existing
   - **Network settings**:
     - Allow SSH (port 22)
     - Allow HTTP (port 80)
     - Allow HTTPS (port 443)
   - **Storage**: 20 GB gp3

3. **Launch** the instance and note the public IP

### Step 2: Connect and Setup

```bash
# Connect to your instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (same as VirtualBox guide)
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER

# Log out and back in
exit
```

### Step 3: Deploy Application

Same as VirtualBox deployment. Copy your files and run docker-compose.

### Step 4: Setup Domain and SSL (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d alerts.yourdomain.com
```

---

## Option 2: ECS Fargate (Production Ready)

This approach uses AWS managed container services for better scalability and reliability.

### Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Route53   │────▶│     ALB      │────▶│ ECS Fargate │
│  (Domain)   │     │(Load Balancer)│     │  (Backend)  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                    │
                           │              ┌─────┴─────┐
                           │              │           │
                           ▼              ▼           ▼
                    ┌──────────────┐ ┌─────────┐ ┌─────────┐
                    │ ECS Fargate  │ │   RDS   │ │Elasticache│
                    │  (Frontend)  │ │(Postgres)│ │ (Redis) │
                    └──────────────┘ └─────────┘ └─────────┘
```

### Prerequisites

- AWS CLI installed and configured
- Docker installed locally
- Terraform (optional, for IaC)

### Step 1: Create ECR Repositories

```bash
# Create repositories for backend and frontend
aws ecr create-repository --repository-name alert-dashboard-backend
aws ecr create-repository --repository-name alert-dashboard-frontend

# Get the repository URIs
export BACKEND_REPO=$(aws ecr describe-repositories --repository-names alert-dashboard-backend --query 'repositories[0].repositoryUri' --output text)
export FRONTEND_REPO=$(aws ecr describe-repositories --repository-names alert-dashboard-frontend --query 'repositories[0].repositoryUri' --output text)
```

### Step 2: Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $BACKEND_REPO

# Build and push backend
cd backend
docker build -t alert-dashboard-backend .
docker tag alert-dashboard-backend:latest $BACKEND_REPO:latest
docker push $BACKEND_REPO:latest

# Build and push frontend
cd ../frontend
docker build -t alert-dashboard-frontend .
docker tag alert-dashboard-frontend:latest $FRONTEND_REPO:latest
docker push $FRONTEND_REPO:latest
```

### Step 3: Create Infrastructure

Create the following AWS resources (via Console or Terraform):

1. **VPC with public/private subnets**
2. **RDS PostgreSQL instance** (db.t3.micro for dev)
3. **ElastiCache Redis cluster** (cache.t3.micro for dev)
4. **Application Load Balancer**
5. **ECS Cluster**
6. **ECS Task Definitions** (backend and frontend)
7. **ECS Services**
8. **Secrets Manager** for sensitive configs

### Step 4: Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "alert-dashboard-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/alert-dashboard-backend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "false"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:alert-dashboard/database-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:alert-dashboard/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/alert-dashboard",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

### Step 5: Terraform (Infrastructure as Code)

For a production setup, use Terraform. Create `main.tf`:

```hcl
# See infrastructure/aws/main.tf for complete example
```

---

## Option 3: Terraform Module (Complete IaC)

For a fully automated deployment, see the `infrastructure/aws/` directory which contains:

- VPC and networking
- RDS PostgreSQL
- ElastiCache Redis
- ECS Fargate cluster
- Application Load Balancer
- Route53 DNS
- ACM SSL certificates
- CloudWatch logging
- IAM roles and policies

---

## Cost Estimation

### EC2 + Docker (us-east-1)
| Resource | Type | Monthly Cost |
|----------|------|--------------|
| EC2 | t3.small | ~$15 |
| EBS | 20GB gp3 | ~$2 |
| **Total** | | **~$17/month** |

### ECS Fargate (us-east-1)
| Resource | Type | Monthly Cost |
|----------|------|--------------|
| Fargate | 0.5 vCPU, 1GB | ~$15 |
| RDS | db.t3.micro | ~$15 |
| ElastiCache | cache.t3.micro | ~$12 |
| ALB | - | ~$16 |
| **Total** | | **~$58/month** |

---

## Security Best Practices

1. **Use VPC** - Deploy in private subnets
2. **Security Groups** - Restrict access to necessary ports only
3. **Secrets Manager** - Store sensitive data securely
4. **IAM Roles** - Use least privilege principle
5. **Enable CloudTrail** - Audit all API calls
6. **Enable GuardDuty** - Threat detection
7. **SSL/TLS** - Always use HTTPS
8. **Regular Updates** - Keep container images updated

---

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions, CodePipeline)
2. Configure CloudWatch alarms
3. Set up automated backups for RDS
4. Implement blue-green deployments
5. Configure auto-scaling policies
