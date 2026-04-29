# Docker Image Publishing and IBM Cloud Code Engine Deployment Guide

This guide provides step-by-step instructions for publishing your PDF Compliance API Docker image to DockerHub and deploying it to IBM Cloud Code Engine.

## Prerequisites

1. **DockerHub Account**: Create a free account at [hub.docker.com](https://hub.docker.com)
2. **IBM Cloud Account**: Sign up at [cloud.ibm.com](https://cloud.ibm.com)
3. **Docker Desktop**: Install Docker on your local machine
4. **IBM Cloud CLI**: Install the IBM Cloud CLI tools

## Part 1: Publishing Docker Image to DockerHub

### Step 1: Login to DockerHub

```bash
docker login
```

Enter your DockerHub username and password when prompted.

### Step 2: Build Your Docker Image

Build the image with your DockerHub username as a prefix:

```bash
# Replace 'rahul1181' with your actual DockerHub username
docker build -t rahul1181/pdf-compliance-api:latest .
```

You can also tag with a specific version:

```bash
docker build -t rahul1181/pdf-compliance-api:v1.0.0 .
```

### Step 3: Test the Image Locally (Optional but Recommended)

```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_api_key_here \
  rahul1181/pdf-compliance-api:latest
```

Test the API at `http://localhost:8000/health`

### Step 4: Push Image to DockerHub

```bash
# Push latest tag
docker push rahul1181/pdf-compliance-api:latest

# Push specific version (if tagged)
docker push rahul1181/pdf-compliance-api:v1.0.0
```

### Step 5: Verify on DockerHub

1. Go to [hub.docker.com](https://hub.docker.com)
2. Navigate to your repositories
3. Confirm your image is listed with the correct tags

## Part 2: Deploying to IBM Cloud Code Engine

### Step 1: Install IBM Cloud CLI

**Linux/macOS:**
```bash
curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
```

**Windows:**
Download from [IBM Cloud CLI](https://cloud.ibm.com/docs/cli?topic=cli-getting-started)

### Step 2: Install Code Engine Plugin

```bash
ibmcloud plugin install code-engine
```

### Step 3: Login to IBM Cloud

```bash
ibmcloud login
```

For SSO or federated ID:
```bash
ibmcloud login --sso
```

### Step 4: Target Your Resource Group and Region

```bash
# List available resource groups
ibmcloud resource groups

# Target a resource group
ibmcloud target -g Default

# List available regions
ibmcloud regions

# Target a region (e.g., us-south)
ibmcloud target -r us-south
```

### Step 5: Create a Code Engine Project

```bash
# Create a new project
ibmcloud ce project create --name pdf-compliance-project

# Or select an existing project
ibmcloud ce project select --name pdf-compliance-project
```

### Step 6: Create Environment Variables Secret

Create a file with your environment variables:

```bash
# Create env-vars.txt
cat > env-vars.txt << EOF
GEMINI_API_KEY=your_actual_gemini_api_key_here
FLASK_ENV=production
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=false
EOF
```

Create a secret in Code Engine:

```bash
ibmcloud ce secret create --name pdf-compliance-secrets --from-env-file env-vars.txt
```

### Step 7: Deploy Application from DockerHub

```bash
ibmcloud ce application create \
  --name pdf-compliance-api \
  --image docker.io/rahul1181/pdf-compliance-api:latest \
  --registry-secret docker.io \
  --env-from-secret pdf-compliance-secrets \
  --port 8000 \
  --min-scale 1 \
  --max-scale 2 \
  --cpu 1 \
  --memory 2G \
  --request-timeout 300
```

**Parameter Explanations:**
- `--name`: Your application name in Code Engine
- `--image`: Full DockerHub image path
- `--registry-secret`: Use `docker.io` for public DockerHub images
- `--env-from-secret`: Reference to the secrets created earlier
- `--port`: Port your application listens on (8000 for this API)
- `--min-scale`: Minimum number of instances (0 for scale-to-zero)
- `--max-scale`: Maximum number of instances
- `--cpu`: CPU allocation per instance
- `--memory`: Memory allocation per instance
- `--request-timeout`: Maximum request timeout in seconds

### Step 8: Get Application URL

```bash
ibmcloud ce application get --name pdf-compliance-api
```

Look for the URL in the output (e.g., `https://pdf-compliance-api.xxx.us-south.codeengine.appdomain.cloud`)

### Step 9: Test Your Deployment

```bash
# Test health endpoint
curl https://your-app-url.codeengine.appdomain.cloud/health

# Test API documentation
curl https://your-app-url.codeengine.appdomain.cloud/docs
```

## Part 3: Using Private DockerHub Images (Optional)

If your DockerHub repository is private:

### Step 1: Create Registry Secret

```bash
ibmcloud ce registry create \
  --name dockerhub-registry \
  --server https://index.docker.io/v1/ \
  --username your_dockerhub_username \
  --password your_dockerhub_password
```

### Step 2: Deploy with Private Registry

```bash
ibmcloud ce application create \
  --name pdf-compliance-api \
  --image docker.io/rahul1181/pdf-compliance-api:latest \
  --registry-secret dockerhub-registry \
  --env-from-secret pdf-compliance-secrets \
  --port 8000 \
  --min-scale 1 \
  --max-scale 5 \
  --cpu 1 \
  --memory 2G
```

## Part 4: Updating Your Application

### Update with New Image Version

```bash
# Build and push new version
docker build -t rahul1181/pdf-compliance-api:v1.0.1 .
docker push rahul1181/pdf-compliance-api:v1.0.1

# Update Code Engine application
ibmcloud ce application update \
  --name pdf-compliance-api \
  --image docker.io/rahul1181/pdf-compliance-api:v1.0.1
```

### Update Environment Variables

```bash
# Update secret
ibmcloud ce secret update --name pdf-compliance-secrets --from-env-file env-vars.txt

# Restart application to pick up changes
ibmcloud ce application update --name pdf-compliance-api
```

## Part 5: Monitoring and Management

### View Application Logs

```bash
# View recent logs
ibmcloud ce application logs --name pdf-compliance-api

# Follow logs in real-time
ibmcloud ce application logs --name pdf-compliance-api --follow
```

### View Application Details

```bash
ibmcloud ce application get --name pdf-compliance-api
```

### List All Applications

```bash
ibmcloud ce application list
```

### Scale Application

```bash
ibmcloud ce application update \
  --name pdf-compliance-api \
  --min-scale 2 \
  --max-scale 10
```

### Delete Application

```bash
ibmcloud ce application delete --name pdf-compliance-api
```

## Part 6: Cost Optimization Tips

1. **Scale to Zero**: Set `--min-scale 0` for development environments
2. **Right-size Resources**: Start with smaller CPU/memory and scale up if needed
3. **Use Request Timeout**: Set appropriate timeouts to prevent hanging requests
4. **Monitor Usage**: Use IBM Cloud monitoring to track resource usage

## Part 7: Troubleshooting

### Application Won't Start

```bash
# Check application events
ibmcloud ce application events --name pdf-compliance-api

# Check logs for errors
ibmcloud ce application logs --name pdf-compliance-api --tail 100
```

### Common Issues

1. **Port Mismatch**: Ensure `--port` matches your Dockerfile EXPOSE port (8000)
2. **Missing Environment Variables**: Verify secrets are created and referenced correctly
3. **Image Pull Errors**: Check registry credentials and image path
4. **Memory Issues**: Increase `--memory` if application crashes
5. **Timeout Errors**: Increase `--request-timeout` for long-running requests

### Health Check Failures

Ensure your application responds to health checks:
```bash
curl https://your-app-url/health
```

## Part 8: CI/CD Integration (Optional)

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to IBM Cloud Code Engine

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and Push Docker Image
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/pdf-compliance-api:${{ github.sha }} .
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/pdf-compliance-api:${{ github.sha }}
      
      - name: Install IBM Cloud CLI
        run: |
          curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
          ibmcloud plugin install code-engine
      
      - name: Deploy to Code Engine
        run: |
          ibmcloud login --apikey ${{ secrets.IBM_CLOUD_API_KEY }} -r us-south
          ibmcloud ce project select --name pdf-compliance-project
          ibmcloud ce application update \
            --name pdf-compliance-api \
            --image docker.io/${{ secrets.DOCKERHUB_USERNAME }}/pdf-compliance-api:${{ github.sha }}
```

## Quick Reference Commands

```bash
# Build and push to DockerHub
docker build -t rahul1181/pdf-compliance-api:latest .
docker push rahul1181/pdf-compliance-api:latest

# Deploy to Code Engine
ibmcloud login
ibmcloud ce project select --name pdf-compliance-project
ibmcloud ce application create \
  --name pdf-compliance-api \
  --image docker.io/rahul1181/pdf-compliance-api:latest \
  --env-from-secret pdf-compliance-secrets \
  --port 8000 \
  --min-scale 1 \
  --max-scale 5

# View logs
ibmcloud ce application logs --name pdf-compliance-api --follow

# Update application
docker build -t rahul1181/pdf-compliance-api:v1.0.1 .
docker push rahul1181/pdf-compliance-api:v1.0.1
ibmcloud ce application update \
  --name pdf-compliance-api \
  --image docker.io/rahul1181/pdf-compliance-api:v1.0.1
```

## Additional Resources

- [IBM Cloud Code Engine Documentation](https://cloud.ibm.com/docs/codeengine)
- [DockerHub Documentation](https://docs.docker.com/docker-hub/)
- [IBM Cloud CLI Reference](https://cloud.ibm.com/docs/cli)
- [Code Engine Pricing](https://cloud.ibm.com/docs/codeengine?topic=codeengine-pricing)

## Support

For issues specific to:
- **Docker**: Check [Docker Documentation](https://docs.docker.com/)
- **IBM Cloud**: Contact [IBM Cloud Support](https://cloud.ibm.com/unifiedsupport/supportcenter)
- **This Application**: Open an issue in the project repository