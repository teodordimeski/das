# 🚀 Quick Start Guide

Get the CryptoInfo application running in 3 simple steps!

## Prerequisites

1. **Install Docker Desktop**
   - Windows/Mac: https://www.docker.com/products/docker-desktop
   - Linux: https://docs.docker.com/engine/install/

2. **Verify Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

## Option 1: Using Start Script (Recommended)

### Linux/Mac
```bash
chmod +x start-docker.sh
./start-docker.sh
```

### Windows
```cmd
start-docker.bat
```

## Option 2: Manual Start

### Start Everything
```bash
docker-compose up --build
```

### Start in Background (Detached)
```bash
docker-compose up -d --build
```

## Access the Application

Once started, open your browser:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api
- **Health Check**: http://localhost:8080/api/health

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Check Status
```bash
docker-compose ps
```

## First Time Setup

The first time you run the application:

1. **Initial startup takes 5-10 minutes**
   - Building Docker images
   - Installing dependencies
   - Initializing database

2. **Database population**
   - Python filters will automatically run
   - Downloads crypto data from Binance
   - May take 10-20 minutes

3. **LSTM models**
   - Models are trained on-demand
   - First prediction takes 2-5 minutes
   - Subsequent predictions are instant

## Troubleshooting

### Port Already in Use
If ports 3000, 8080, or 5432 are in use:

```bash
# Find what's using the port
lsof -i :8080  # Mac/Linux
netstat -ano | findstr :8080  # Windows

# Stop the process or change ports in docker-compose.yml
```

### Services Not Starting
```bash
# Check logs
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Database Connection Issues
```bash
# Restart postgres
docker-compose restart postgres

# Check if postgres is healthy
docker-compose ps
```

## Next Steps

- Read [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) for cloud deployment
- Check application health: http://localhost:8080/api/health
- Explore the API endpoints in your browser

## Need Help?

Check the logs first:
```bash
docker-compose logs -f
```

Common issues are documented in [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md#-troubleshooting)

