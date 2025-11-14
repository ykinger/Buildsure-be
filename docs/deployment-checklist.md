# AWS ECS Deployment Checklist

Use this checklist to verify your deployment setup is complete.

## ✅ Pre-Deployment Checklist

### 1. AWS Resources Created
- [ ] **ECR Repository** created (`buildsure-api`)
- [ ] **ECS Cluster** created (`buildsure-cluster`)
- [ ] **ECS Task Definition** created (`buildsure-api-task`)
- [ ] **ECS Service** created (`buildsure-api-service`)
- [ ] **Application Load Balancer** created (optional)
- [ ] **Target Group** configured with health check path `/api/v1/health/simple`
- [ ] **RDS PostgreSQL** instance running

### 2. IAM Configuration
- [ ] IAM user created for GitHub Actions (`github-actions-deployer`)
- [ ] `AmazonEC2ContainerRegistryPowerUser` policy attached
- [ ] `AmazonECS_FullAccess` policy attached (or custom policy)
- [ ] Access keys generated and saved securely

### 3. Security Groups
- [ ] **ALB Security Group**: Allows inbound HTTP/HTTPS from 0.0.0.0/0
- [ ] **ECS Security Group**: Allows inbound 8000 from ALB security group
- [ ] **RDS Security Group**: Allows inbound 5432 from ECS security group

### 4. ECS Task Definition Environment Variables
Set these in your task definition:
- [ ] `ASYNC_DATABASE_URL` - PostgreSQL connection string
- [ ] `GEMINI_API_KEY` - Your Gemini API key
- [ ] `COGNITO_REGION` - us-east-2
- [ ] `COGNITO_USER_POOL_ID` - us-east-2_uM4bmGp4F
- [ ] `COGNITO_APP_CLIENT_ID` - 1jnked1f39lijtnhkc2j69f4c9
- [ ] `SQL_ECHO` - false
- [ ] `DEBUG` - false

### 5. GitHub Secrets
Navigate to: **Settings → Secrets and variables → Actions**

Add these secrets:
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`

### 6. Workflow Configuration
Verify these values in `.github/workflows/deploy-ecs.yml`:
- [ ] `AWS_REGION: us-east-2`
- [ ] `ECR_REPOSITORY: buildsure-api`
- [ ] `ECS_SERVICE: buildsure-api-service`
- [ ] `ECS_CLUSTER: buildsure-cluster`
- [ ] `ECS_TASK_DEFINITION: buildsure-api-task`
- [ ] `CONTAINER_NAME: buildsure-api`

Update if your resource names differ.

## 🚀 First Deployment

### Test Manual Deployment
1. [ ] Commit and push workflow files to `main` branch:
   ```bash
   git add .github/workflows/deploy-ecs.yml
   git commit -m "Add ECS deployment pipeline"
   git push origin main
   ```

2. [ ] Go to GitHub **Actions** tab
3. [ ] Watch the workflow run
4. [ ] Verify all steps complete successfully

### Verify Deployment
1. [ ] Check ECS service has running task
2. [ ] Check CloudWatch logs for application startup
3. [ ] Test health check endpoint:
   ```bash
   curl http://your-alb-dns-name/api/v1/health/simple
   ```
4. [ ] Test API endpoints through ALB

## 🔍 Post-Deployment Verification

### Application Health
- [ ] Health check returns 200 OK
- [ ] Application logs show successful startup
- [ ] Database connection successful
- [ ] No errors in CloudWatch logs

### Load Balancer
- [ ] Target group shows healthy targets
- [ ] ALB accessible from internet (if public)
- [ ] HTTPS working (if configured)

### Monitoring
- [ ] CloudWatch log group created: `/ecs/buildsure-api-task`
- [ ] Application logs visible in CloudWatch
- [ ] ECS service metrics available

## 🐛 Common Issues

### Pipeline Fails - "Cannot find repository"
**Solution**: Verify ECR repository name matches in workflow and AWS

### Pipeline Fails - "Access Denied"
**Solution**: Check IAM permissions and GitHub Secrets are correct

### ECS Task Won't Start
**Solution**: Check environment variables and RDS security group

### Health Check Fails
**Solution**: 
- Verify target group health check path: `/api/v1/health/simple`
- Check ECS security group allows traffic from ALB
- Review CloudWatch logs for application errors

### Database Connection Error
**Solution**:
- Verify RDS security group allows 5432 from ECS security group
- Check `ASYNC_DATABASE_URL` format is correct
- Ensure RDS is in same VPC as ECS tasks

## 📚 Documentation

- **Detailed Guide**: [AWS Deployment Guide](./aws-deployment-guide.md)
- **Workflow Info**: [GitHub Workflows README](../.github/workflows/README.md)

## 🎯 Next Steps

Once deployment is working:
- [ ] Set up staging environment
- [ ] Configure auto-scaling
- [ ] Set up CloudWatch alarms
- [ ] Configure backup strategy
- [ ] Document runbook procedures
- [ ] Set up monitoring dashboards

## 📞 Need Help?

If you encounter issues:
1. Check the detailed [AWS Deployment Guide](./aws-deployment-guide.md)
2. Review GitHub Actions logs
3. Check CloudWatch logs
4. Review ECS service events
5. Verify security group rules
