# 🐳 Docker Setup - Complete Summary

## 📦 What Was Created

Your application now has a complete Docker containerization setup with the following files:

### Core Docker Files

1. **`docker-compose.yml`** - Main orchestration file
   - Defines 3 services: PostgreSQL, Backend (Spring Boot), Frontend (React)
   - Networks them together
   - Manages volumes for data persistence
   - Configures environment variables

2. **`Dockerfile.backend`** - Backend container
   - Multi-stage build for optimization
   - Java 17 + Python 3 environment
   - Installs all Python dependencies (TensorFlow, pandas, etc.)
   - Copies application code and Python filters

3. **`crypto-frontend/Dockerfile`** - Frontend container
   - Multi-stage build: Build with Node.js, serve with Nginx
   - Optimized production build
   - Minimal final image size

4. **`crypto-frontend/nginx.conf`** - Nginx configuration
   - Serves React app
   - Handles SPA routing
   - Enables gzip compression
   - Security headers

5. **`.dockerignore`** - Excludes unnecessary files from Docker builds
   - Keeps images small and builds fast

6. **`application-docker.properties`** - Spring Boot config for Docker
   - Database connection to Docker network
   - Python command configuration

### Helper Files

7. **`start-docker.sh`** (Linux/Mac) - One-click startup script
8. **`start-docker.bat`** (Windows) - One-click startup script
9. **`QUICKSTART.md`** - Quick reference guide
10. **`DOCKER_DEPLOYMENT.md`** - Complete deployment guide

## 🚀 How to Use It

### Quick Start (3 Steps)

1. **Make sure Docker Desktop is running**

2. **Navigate to project directory**
   ```bash
   cd "/Users/teodordimeski/Documents/Faks/semestar V/dizajn i arhitektura na softver/domasni/temp-das-repo/Domasna4"
   ```

3. **Run the start script**
   ```bash
   # Linux/Mac
   ./start-docker.sh
   
   # Windows
   start-docker.bat
   
   # Or manually
   docker-compose up --build
   ```

### First Time Setup

The first run will:
1. Download base Docker images (PostgreSQL, Node, Java)
2. Build your custom images
3. Install all dependencies
4. Start all services
5. Initialize the database
6. Run Python filters to populate data

**Total time: 10-15 minutes**

### Access Your Application

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api
- **Health Check**: http://localhost:8080/api/health
- **Database**: localhost:5432 (postgres/admin)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Frontend   │  │   Backend    │  │ PostgreSQL│ │
│  │   (Nginx)    │  │  (Spring+Py) │  │           │ │
│  │              │  │              │  │           │ │
│  │  Port: 80    │  │  Port: 8080  │  │ Port: 5432│ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│         │                  │                │        │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
     Host:3000          Host:8080        Host:5432
```

## 📊 Service Details

### 1. PostgreSQL Database (`postgres`)
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Credentials**: postgres/admin
- **Volume**: `postgres_data` (persisted)
- **Health Check**: Automatic
- **Database**: cryptoCoins

### 2. Spring Boot Backend (`backend`)
- **Build**: Custom from `Dockerfile.backend`
- **Base**: Java 17 + Python 3
- **Port**: 8080
- **Dependencies**: 
  - TensorFlow 2.15+
  - pandas, numpy, scikit-learn
  - psycopg2, SQLAlchemy
- **Volumes**: 
  - `./lstm_models` - Trained LSTM models
  - `./python_filters/lstm_models` - Model cache
- **Health Check**: `/api/health` endpoint

### 3. React Frontend (`frontend`)
- **Build**: Node 18 → Nginx Alpine
- **Port**: 3000 (mapped from Nginx port 80)
- **Features**:
  - Production optimized build
  - Gzip compression
  - SPA routing support
  - Security headers

## 🛠️ Common Commands

### Startup
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start with rebuild
docker-compose up --build
```

### Monitoring
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Check service status
docker-compose ps

# Check resource usage
docker stats
```

### Management
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v

# Restart a service
docker-compose restart backend

# Rebuild a service
docker-compose up -d --build backend
```

### Debugging
```bash
# Execute command in container
docker exec -it cryptoinfo-backend sh
docker exec -it cryptoinfo-postgres psql -U postgres -d cryptoCoins

# View container details
docker inspect cryptoinfo-backend

# Test network connectivity
docker exec cryptoinfo-backend ping postgres
```

## ☁️ Cloud Deployment Options

### AWS Deployment
1. **ECS (Elastic Container Service)** - Recommended
   - Push images to ECR
   - Use RDS for PostgreSQL
   - Create ECS cluster and task definitions
   - Deploy behind Application Load Balancer

2. **EC2 with Docker Compose**
   - Launch EC2 instance
   - Install Docker & Docker Compose
   - Copy project files
   - Run `docker-compose up -d`

3. **Elastic Beanstalk**
   - Use `docker-compose.yml`
   - Deploy with EB CLI

### Azure Deployment
1. **Azure Container Instances (ACI)** - Easiest
   - Push to Azure Container Registry
   - Use Azure Database for PostgreSQL
   - Deploy container group

2. **Azure App Service**
   - Deploy as web app containers
   - Use managed PostgreSQL

3. **Azure VM with Docker Compose**
   - Similar to EC2 approach

### Production Checklist
- [ ] Change database password
- [ ] Use managed database service (RDS/Azure DB)
- [ ] Set up SSL/HTTPS certificates
- [ ] Configure domain names
- [ ] Set up monitoring and alerts
- [ ] Configure backups
- [ ] Set up CI/CD pipeline
- [ ] Implement secrets management
- [ ] Configure auto-scaling
- [ ] Set up CDN for frontend

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # Database
  POSTGRES_DB: cryptoCoins
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: admin  # CHANGE IN PRODUCTION!
  
  # Backend
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/cryptoCoins
  
  # Python
  PYTHON_COMMAND: python3
```

### Port Mapping

Change ports in `docker-compose.yml`:

```yaml
ports:
  - "3000:80"   # Frontend: HOST:CONTAINER
  - "8080:8080" # Backend
  - "5432:5432" # Database
```

## 📈 Performance Optimization

### For Development
- Use Docker BuildKit for faster builds
- Enable Docker layer caching
- Use volumes for live code reloading

### For Production
- Use specific version tags (not `:latest`)
- Multi-stage builds (already implemented)
- Minimize image layers
- Use Alpine base images (already using)
- Configure resource limits
- Set up horizontal scaling

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process
lsof -i :8080  # Mac/Linux
netstat -ano | findstr :8080  # Windows

# Change port in docker-compose.yml
```

### Database Connection Failed
```bash
# Check if postgres is healthy
docker-compose ps

# Restart postgres
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Out of Memory
```bash
# Increase Docker Desktop memory
# Settings → Resources → Memory → 4GB+

# Or add to docker-compose.yml
services:
  backend:
    mem_limit: 2g
```

### Build Failed
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Container Keeps Restarting
```bash
# Check logs
docker-compose logs backend

# Check health
docker inspect cryptoinfo-backend
```

## 📝 File Structure

```
Domasna4/
├── docker-compose.yml          # Main orchestration
├── Dockerfile.backend          # Backend container
├── .dockerignore               # Exclude from builds
│
├── crypto-frontend/
│   ├── Dockerfile              # Frontend container
│   ├── nginx.conf              # Nginx config
│   └── .dockerignore
│
├── src/main/resources/
│   └── application-docker.properties
│
├── start-docker.sh             # Linux/Mac launcher
├── start-docker.bat            # Windows launcher
│
├── DOCKER_DEPLOYMENT.md        # Full deployment guide
├── QUICKSTART.md               # Quick reference
└── DOCKER_SETUP_SUMMARY.md     # This file
```

## 🎯 Next Steps

1. **Test Locally**
   ```bash
   ./start-docker.sh
   # Visit http://localhost:3000
   ```

2. **Review Logs**
   ```bash
   docker-compose logs -f
   ```

3. **Test API**
   ```bash
   curl http://localhost:8080/api/health
   ```

4. **Prepare for Cloud**
   - Read `DOCKER_DEPLOYMENT.md`
   - Choose cloud provider (AWS/Azure)
   - Set up accounts and CLI tools
   - Configure production secrets

5. **Deploy**
   - Follow cloud-specific guide in `DOCKER_DEPLOYMENT.md`
   - Set up monitoring
   - Configure backups
   - Test thoroughly

## 💡 Tips

- Keep `postgres_data` volume for data persistence
- Use `.env` file for sensitive configuration (not committed to git)
- Monitor logs regularly: `docker-compose logs -f`
- Update images periodically: `docker-compose pull`
- Back up your database before major changes
- Test locally before deploying to cloud

## 📚 Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **AWS ECS**: https://aws.amazon.com/ecs/
- **Azure Containers**: https://azure.microsoft.com/en-us/products/container-instances/

## ✅ Success Indicators

Your setup is working correctly when:
- ✅ All 3 services show "Up" in `docker-compose ps`
- ✅ Frontend loads at http://localhost:3000
- ✅ Health check returns OK at http://localhost:8080/api/health
- ✅ No errors in `docker-compose logs`
- ✅ Database has crypto data (may take 10-20 min on first run)

## 🆘 Getting Help

1. Check logs: `docker-compose logs -f`
2. Verify status: `docker-compose ps`
3. Read troubleshooting section above
4. Check Docker Desktop settings (memory, disk space)
5. Review `DOCKER_DEPLOYMENT.md` for detailed info

---

**Your application is now fully containerized and ready for deployment!** 🎉

Start with `./start-docker.sh` and visit http://localhost:3000

