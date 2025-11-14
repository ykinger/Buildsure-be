# AWS ECS Deployment Guide

This guide walks you through deploying the BuildSure API to AWS ECS using GitHub Actions.

## Prerequisites

You should have already created the following AWS resources:
- ✅ ECR Repository (`buildsure-api`)
- ✅ ECS Cluster (`buildsure-cluster`)
- ✅ ECS Task Definition (`buildsure-api-task`)
- ✅ ECS Service (`buildsure-api-service`)
- ✅ Application Load Balancer (optional)
- ✅ RDS PostgreSQL Database
- ✅ IAM User with deployment permissions

## GitHub Secrets Setup

Before the pipeline can run, you need to configure GitHub Secrets:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add the following:

### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM user access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM user secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

### Verify Environment Variables in Workflow

The workflow is pre-configured with the following values in `.github/workflows/deploy-ecs.yml`:

```yaml
env:
  AWS_REGION: us-east-2
  ECR_REPOSITORY: buildsure-api
  ECS_SERVICE: buildsure-api-service
  ECS_CLUSTER: buildsure-cluster
  ECS_TASK_DEFINITION: buildsure-api-task
  CONTAINER_NAME: buildsure-api
```

**Important**: If your resource names differ, update these values in the workflow file.

## ECS Task Definition Environment Variables

Make sure your ECS Task Definition includes these environment variables:

```
ASYNC_DATABASE_URL=postgresql+asyncpg://username:password@your-rds-endpoint:5432/buildsure
GEMINI_API_KEY=your-gemini-api-key
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_uM4bmGp4F
COGNITO_APP_CLIENT_ID=1jnked1f39lijtnhkc2j69f4c9
SQL_ECHO=false
DEBUG=false
```

You can set these in the AWS Console:
1. Go to **ECS** → **Task Definitions** → **buildsure-api-task**
2. Click **Create new revision**
3. Under **Container definitions**, edit the `buildsure-api` container
4. Scroll to **Environment variables**
5. Add all required variables
6. Save and create new revision

Alternatively, use AWS Secrets Manager for sensitive values:
1. Create secrets in AWS Secrets Manager
2. Reference them in your task definition using `valueFrom` instead of `value`

## Deployment Workflow

### Automatic Deployment

The pipeline automatically triggers on:
- **Push to main branch**: Any commit pushed to the `main` branch will trigger a deployment

### Manual Deployment

You can also trigger deployments manually:
1. Go to **Actions** tab in your GitHub repository
2. Select **Deploy to AWS ECS** workflow
3. Click **Run workflow**
4. Choose the branch (usually `main`)
5. Click **Run workflow** button

## Deployment Process

The workflow performs these steps:

1. **Checkout Code**: Pulls the latest code from the repository
2. **Configure AWS**: Sets up AWS credentials
3. **Login to ECR**: Authenticates with Elastic Container Registry
4. **Build Docker Image**: Builds the Docker image from your Dockerfile
5. **Push to ECR**: Pushes two tags:
   - `{commit-sha}` - Specific version
   - `latest` - Latest version
6. **Update Task Definition**: Downloads current task definition and updates image
7. **Deploy to ECS**: Deploys new task definition to ECS service
8. **Wait for Stability**: Waits for service to reach steady state

## Monitoring Deployment

### GitHub Actions

1. Go to **Actions** tab in your repository
2. Click on the running workflow
3. Monitor each step's progress
4. Check the deployment summary at the end

### AWS Console

Monitor the deployment in AWS:

1. **ECS Service**:
   - Go to **ECS** → **Clusters** → **buildsure-cluster** → **buildsure-api-service**
   - Check the **Deployments** tab
   - Monitor **Events** tab for status updates

2. **CloudWatch Logs**:
   - Go to **CloudWatch** → **Log Groups**
   - Find `/ecs/buildsure-api-task`
   - View container logs in real-time

3. **Load Balancer**:
   - Go to **EC2** → **Load Balancers**
   - Check target health status
   - View request metrics

## Health Check

Your application includes a health check endpoint at `/api/v1/health/simple`.

Test it after deployment:
```bash
curl http://your-alb-dns-name/api/v1/health/simple
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Rollback

If a deployment fails or introduces issues:

### Option 1: Revert Code and Redeploy
```bash
git revert <commit-hash>
git push origin main
```
This triggers a new deployment with the previous working code.

### Option 2: Manual Rollback via AWS Console
1. Go to **ECS** → **Clusters** → **buildsure-cluster** → **buildsure-api-service**
2. Click **Update service**
3. Under **Revision**, select a previous task definition revision
4. Click **Update**

### Option 3: Deploy Specific Image Tag
Update the workflow to use a specific image tag:
```bash
aws ecs update-service \
  --cluster buildsure-cluster \
  --service buildsure-api-service \
  --task-definition buildsure-api-task:X
```

## Troubleshooting

### Deployment Fails at Build Step
- Check Dockerfile syntax
- Verify all files are committed to the repository
- Check GitHub Actions logs for specific error

### Deployment Fails at Push to ECR
- Verify ECR repository exists and name matches
- Check IAM permissions for ECR access
- Ensure AWS credentials are correct in GitHub Secrets

### Deployment Fails at ECS Update
- Verify ECS cluster, service, and task definition names
- Check IAM permissions for ECS access
- Review ECS service events for specific errors

### Application Won't Start
- Check CloudWatch logs for application errors
- Verify environment variables in task definition
- Ensure RDS security group allows traffic from ECS tasks
- Verify database connection string is correct

### Health Check Fails
- Verify health check path in ALB target group: `/api/v1/health/simple`
- Check security groups allow traffic: ALB → ECS Tasks
- Review application logs in CloudWatch

### Database Connection Issues
- Verify RDS security group allows inbound 5432 from ECS security group
- Check `ASYNC_DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:5432/db`
- Ensure RDS is in the same VPC as ECS tasks
- Verify database credentials are correct

## Security Best Practices

1. **Secrets Management**:
   - Store sensitive values in AWS Secrets Manager
   - Reference secrets in task definition using `valueFrom`
   - Never commit secrets to git

2. **IAM Permissions**:
   - Use least privilege principle
   - Create separate IAM user for GitHub Actions
   - Rotate access keys regularly

3. **Network Security**:
   - Use private subnets for ECS tasks (if using NAT Gateway)
   - Restrict security group rules to minimum required
   - Use ALB to expose only necessary endpoints

4. **Container Security**:
   - Regularly update base images
   - Scan images for vulnerabilities
   - Use non-root user in Dockerfile (already configured)

## Cost Optimization

- **Fargate Spot**: Consider Fargate Spot for 70% cost savings (with potential interruptions)
- **Right-sizing**: Monitor CPU/memory usage and adjust task definition
- **Auto-scaling**: Set up auto-scaling based on CPU/memory metrics
- **Log Retention**: Set CloudWatch log retention period (default is indefinite)

## Next Steps

Once your pipeline is working:

1. **Add Staging Environment**:
   - Create separate ECS service for staging
   - Add staging workflow that deploys on `develop` branch
   - Test changes in staging before production

2. **Enable Auto-scaling**:
   - Set up target tracking scaling policy
   - Scale based on CPU, memory, or request count

3. **Add Monitoring**:
   - Set up CloudWatch alarms for errors
   - Configure SNS notifications
   - Set up AWS X-Ray for tracing

4. **Improve CI/CD**:
   - Add automated tests before deployment
   - Add code quality checks (linting, security scanning)
   - Implement blue-green or canary deployments

## Support

For issues or questions:
- Check GitHub Actions logs
- Review CloudWatch logs
- Check AWS ECS console for service status
- Review this documentation

## References

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)
