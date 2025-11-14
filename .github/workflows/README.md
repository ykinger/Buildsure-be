# GitHub Actions Workflows

This directory contains CI/CD workflows for the BuildSure API.

## Available Workflows

### `deploy-ecs.yml` - Deploy to AWS ECS

Automatically deploys the application to AWS ECS on Fargate.

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**What it does:**
1. Builds Docker image from Dockerfile
2. Pushes image to AWS ECR
3. Updates ECS task definition
4. Deploys to ECS service
5. Waits for deployment stability

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID` - AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for deployment

**Configuration:**
All environment variables are configured at the top of `deploy-ecs.yml`:
```yaml
env:
  AWS_REGION: us-east-2
  ECR_REPOSITORY: buildsure-api
  ECS_SERVICE: buildsure-api-service
  ECS_CLUSTER: buildsure-cluster
  ECS_TASK_DEFINITION: buildsure-api-task
  CONTAINER_NAME: buildsure-api
```

Update these values if your AWS resource names differ.

## Running Workflows

### Automatic Deployment
Simply push to the `main` branch:
```bash
git push origin main
```

### Manual Deployment
1. Go to **Actions** tab in GitHub
2. Select **Deploy to AWS ECS**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Monitoring

View workflow runs in the **Actions** tab of your GitHub repository.

Each run shows:
- Build logs
- Deployment progress
- Success/failure status
- Deployment summary with image tag and commit info

## Documentation

For detailed setup instructions and troubleshooting, see:
- [AWS Deployment Guide](../../docs/aws-deployment-guide.md)

## Prerequisites

Before workflows can run successfully:
1. AWS infrastructure must be created (ECR, ECS, etc.)
2. GitHub Secrets must be configured
3. IAM permissions must be set up correctly

See the [AWS Deployment Guide](../../docs/aws-deployment-guide.md) for complete setup instructions.
