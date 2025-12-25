# Docker Deployment Guide

This guide explains how to deploy the CryptoInfo application using Docker and Docker Compose for local development, AWS, or Azure.

## 📋 Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose 2.0+ installed
- At least 4GB RAM available for Docker
- 10GB free disk space

### Installation Links
- **Docker Desktop**: https://www.docker.com/products/docker-desktop
- **Docker for Linux**: https://docs.docker.com/engine/install/

## 🚀 Quick Start (Local Development)

### 1. Clone and Navigate to Project
```bash
cd /path/to/Domasna4
```

### 2. Build and Start All Services
```bash
docker-compose up --build
```

This command will:
- Build the backend (Spring Boot + Python)
- Build the frontend (React)
- Start PostgreSQL database
- Network all services together

### 3. Wait for Services to Start
Watch the logs until you see:
```
cryptoinfo-backend   | Started CryptoInfoApplication
cryptoinfo-frontend  | /docker-entrypoint.sh: Launching /docker-entrypoint.d/...
cryptoinfo-postgres  | database system is ready to accept connections
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api
- **Health Check**: http://localhost:8080/api/health
- **PostgreSQL**: localhost:5432 (username: postgres, password: admin)

## 🛠️ Docker Commands

### Start Services (detached mode)
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove All Data (including database)
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose up -d --build backend

# Rebuild all services
docker-compose up -d --build
```

### Check Service Status
```bash
docker-compose ps
```

### Execute Commands in Running Containers
```bash
# Access backend shell
docker exec -it cryptoinfo-backend sh

# Access database
docker exec -it cryptoinfo-postgres psql -U postgres -d cryptoCoins

# Run Python script
docker exec -it cryptoinfo-backend python3 python_filters/predict.py BTCUSDT
```

## 🔧 Configuration

### Environment Variables

You can customize the deployment by editing `docker-compose.yml`:

**Database Configuration:**
```yaml
environment:
  POSTGRES_DB: cryptoCoins
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: admin  # Change for production!
```

**Backend Configuration:**
```yaml
environment:
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/cryptoCoins
  SPRING_DATASOURCE_USERNAME: postgres
  SPRING_DATASOURCE_PASSWORD: admin  # Change for production!
```

### Port Mapping

To change ports, edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8080"  # Change left side: "HOST_PORT:CONTAINER_PORT"
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Option 1: AWS ECS (Elastic Container Service)

1. **Install AWS CLI and Configure**
```bash
aws configure
```

2. **Create ECR Repositories**
```bash
# Create repositories for each service
aws ecr create-repository --repository-name cryptoinfo-backend
aws ecr create-repository --repository-name cryptoinfo-frontend
```

3. **Build and Push Images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -f Dockerfile.backend -t cryptoinfo-backend .
docker build -f crypto-frontend/Dockerfile -t cryptoinfo-frontend ./crypto-frontend

# Tag images
docker tag cryptoinfo-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cryptoinfo-backend:latest
docker tag cryptoinfo-frontend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cryptoinfo-frontend:latest

# Push images
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cryptoinfo-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cryptoinfo-frontend:latest
```

4. **Create RDS PostgreSQL Database**
```bash
aws rds create-db-instance \
  --db-instance-identifier cryptoinfo-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20
```

5. **Create ECS Task Definition and Service**
- Use AWS Console or CLI to create ECS cluster
- Define task definitions using your ECR images
- Set environment variables to point to RDS
- Create Application Load Balancer
- Deploy services

#### Option 2: AWS EC2 with Docker Compose

1. **Launch EC2 Instance**
- Amazon Linux 2 or Ubuntu
- t2.medium or larger
- Security group: Allow ports 80, 443, 8080, 3000, 22

2. **SSH into Instance**
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

3. **Install Docker and Docker Compose**
```bash
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4. **Copy Project Files**
```bash
scp -i your-key.pem -r /path/to/Domasna4 ec2-user@your-instance-ip:~/
```

5. **Start Application**
```bash
cd Domasna4
docker-compose up -d
```

### Azure Deployment

#### Option 1: Azure Container Instances (ACI)

1. **Install Azure CLI**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login
```

2. **Create Resource Group**
```bash
az group create --name cryptoinfo-rg --location eastus
```

3. **Create Azure Container Registry (ACR)**
```bash
az acr create --resource-group cryptoinfo-rg --name cryptoinfoacr --sku Basic
az acr login --name cryptoinfoacr
```

4. **Build and Push Images**
```bash
# Build images
docker build -f Dockerfile.backend -t cryptoinfo-backend .
docker build -f crypto-frontend/Dockerfile -t cryptoinfo-frontend ./crypto-frontend

# Tag for ACR
docker tag cryptoinfo-backend cryptoinfoacr.azurecr.io/backend:latest
docker tag cryptoinfo-frontend cryptoinfoacr.azurecr.io/frontend:latest

# Push to ACR
docker push cryptoinfoacr.azurecr.io/backend:latest
docker push cryptoinfoacr.azurecr.io/frontend:latest
```

5. **Create Azure Database for PostgreSQL**
```bash
az postgres server create \
  --resource-group cryptoinfo-rg \
  --name cryptoinfo-db \
  --location eastus \
  --admin-user postgres \
  --admin-password YOUR_PASSWORD \
  --sku-name B_Gen5_1
```

6. **Deploy with Azure Container Instances**
```bash
# Deploy using docker-compose.yml
az container create --resource-group cryptoinfo-rg --file docker-compose.yml
```

#### Option 2: Azure App Service

1. **Create App Service Plan**
```bash
az appservice plan create \
  --name cryptoinfo-plan \
  --resource-group cryptoinfo-rg \
  --is-linux \
  --sku B1
```

2. **Deploy Containers**
```bash
# Backend
az webapp create \
  --resource-group cryptoinfo-rg \
  --plan cryptoinfo-plan \
  --name cryptoinfo-backend \
  --deployment-container-image-name cryptoinfoacr.azurecr.io/backend:latest

# Frontend
az webapp create \
  --resource-group cryptoinfo-rg \
  --plan cryptoinfo-plan \
  --name cryptoinfo-frontend \
  --deployment-container-image-name cryptoinfoacr.azurecr.io/frontend:latest
```

#### Option 3: Azure VM with Docker Compose

1. **Create VM**
```bash
az vm create \
  --resource-group cryptoinfo-rg \
  --name cryptoinfo-vm \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys
```

2. **Open Ports**
```bash
az vm open-port --port 80 --resource-group cryptoinfo-rg --name cryptoinfo-vm
az vm open-port --port 8080 --resource-group cryptoinfo-rg --name cryptoinfo-vm
az vm open-port --port 3000 --resource-group cryptoinfo-rg --name cryptoinfo-vm
```

3. **SSH and Install Docker**
```bash
ssh azureuser@VM_PUBLIC_IP

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

4. **Deploy Application**
```bash
# Copy files (from local machine)
scp -r /path/to/Domasna4 azureuser@VM_PUBLIC_IP:~/

# On VM
cd Domasna4
docker-compose up -d
```

## 🔒 Production Considerations

### Security Checklist
- [ ] Change default database password
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault)
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Enable container security scanning
- [ ] Set up monitoring and logging
- [ ] Use private networks for service communication
- [ ] Implement rate limiting
- [ ] Enable database backups

### Performance Optimization
- [ ] Use production database instance (not alpine)
- [ ] Configure connection pooling
- [ ] Set up CDN for frontend assets
- [ ] Enable caching (Redis)
- [ ] Configure auto-scaling
- [ ] Use multi-stage builds to minimize image size
- [ ] Implement health checks and readiness probes

### Monitoring Setup
```yaml
# Add to docker-compose.yml for monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs backend

# Check container status
docker ps -a

# Inspect container
docker inspect cryptoinfo-backend
```

### Database Connection Issues
```bash
# Test database connection
docker exec -it cryptoinfo-postgres psql -U postgres -d cryptoCoins

# Check network connectivity
docker exec -it cryptoinfo-backend ping postgres
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8080
netstat -ano | findstr :8080  # Windows

# Stop the process or change port in docker-compose.yml
```

### Out of Memory
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or add to docker-compose.yml:
services:
  backend:
    mem_limit: 2g
```

### Python Dependencies Issues
```bash
# Rebuild backend with no cache
docker-compose build --no-cache backend
```

## 📊 Resource Requirements

### Minimum
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

### Recommended
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB

## 📝 Additional Notes

- The first startup will take 5-10 minutes as Python filters populate the database
- LSTM models will be trained on first prediction request
- Models are persisted in Docker volumes
- Database data is persisted in a named volume
- For production, use managed databases (RDS, Azure Database)

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify all services are healthy: `docker-compose ps`
3. Check connectivity: `docker network inspect domasna4_cryptoinfo-network`

## 📚 Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)

