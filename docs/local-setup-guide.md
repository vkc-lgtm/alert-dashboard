# Local Development Setup Guide

This guide walks you through setting up the Alert Dashboard on your local machine (Windows, Mac, or Linux).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Running the Application](#running-the-application)
4. [Accessing the Dashboard](#accessing-the-dashboard)
5. [Development Workflow](#development-workflow)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Docker Desktop

Docker runs the application in containers, ensuring it works the same on any machine.

**Windows Installation:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. **Important for Windows**: Enable WSL 2 when prompted (or install it first)
   - Open PowerShell as Administrator and run:
     ```powershell
     wsl --install
     ```
   - Restart your computer
4. After restart, open Docker Desktop
5. Wait for Docker to start (you'll see "Docker Desktop is running" in the system tray)

**Verify Docker is installed:**
```powershell
docker --version
docker compose version
```

### 2. Node.js and npm

Required for building and running the frontend application.

**Windows Installation:**
1. Download from: https://nodejs.org/ (LTS version recommended)
2. Run the installer
3. Accept all defaults and complete the installation
4. Restart your terminal/PowerShell
5. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### 3. Git (Optional but Recommended)

For version control and easier project management.

**Windows Installation:**
1. Download from: https://git-scm.com/download/win
2. Run installer with default options
3. Verify: `git --version`

### 3. Text Editor / IDE

Recommended: **Visual Studio Code**
- Download from: https://code.visualstudio.com/
- Useful extensions:
  - Python
  - ES7+ React/Redux/React-Native snippets
  - Docker
  - Prettier

---

## Installation Steps

### Step 1: Get the Project Files

**Option A: If you have the files locally**
- Copy the entire `Alert Dashboard` folder to your desired location
- Example: `C:\Projects\Alert Dashboard`

**Option B: If using Git**
```powershell
cd C:\Projects
git clone <your-repo-url> "Alert Dashboard"
cd "Alert Dashboard"
```

### Step 2: Create Environment Files

The application needs configuration files to run. Create these from the examples provided.

**Windows (PowerShell):**
```powershell
# Navigate to project
cd "C:\Projects\Alert Dashboard"

# Copy backend environment file
Copy-Item backend\.env.example backend\.env

# Copy frontend environment file
Copy-Item frontend\.env.example frontend\.env
```

**Windows (Command Prompt):**
```cmd
cd "C:\Projects\Alert Dashboard"
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

### Step 3: Review Configuration (Optional)

Open `backend\.env` in a text editor. The default settings work for local development:

```env
# These defaults are fine for local development
APP_NAME=Alert Dashboard
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production
API_KEY=your-webhook-api-key-change-in-production

# Database (Docker will create this automatically)
DATABASE_URL=postgresql+asyncpg://alertuser:alertpass@db:5432/alertdb

# Redis (Docker will create this automatically)
REDIS_URL=redis://redis:6379/0
```

**Note:** For local development, the default values are fine. Change them for production!

---

## Running the Application

### Step 1: Open Terminal in Project Directory

**Windows:**
- Open PowerShell or Command Prompt
- Navigate to project:
  ```powershell
  cd "C:\Projects\Alert Dashboard"
  ```

**Or in VS Code:**
- Open the project folder in VS Code
- Press `` Ctrl+` `` to open integrated terminal

### Step 2: Start All Services

Run this single command to start everything:

```powershell
docker compose up -d --build
```

**What this does:**
- `docker compose` - Docker's tool for running multi-container apps
- `up` - Start the services
- `-d` - Run in background (detached mode)
- `--build` - Build the images first

**First run will take 5-10 minutes** as it downloads base images and installs dependencies.

### Step 3: Check Services are Running

```powershell
docker compose ps
```

You should see something like:
```
NAME              STATUS          PORTS
alert-backend     Up              0.0.0.0:8000->8000/tcp
alert-frontend    Up              0.0.0.0:3000->80/tcp
alert-db          Up (healthy)    0.0.0.0:5432->5432/tcp
alert-redis       Up (healthy)    0.0.0.0:6379->6379/tcp
```

### Step 4: View Logs (Optional)

To see what's happening inside the containers:

```powershell
# All services
docker compose logs -f

# Just backend
docker compose logs -f backend

# Just frontend
docker compose logs -f frontend
```

Press `Ctrl+C` to stop viewing logs.

---

## Accessing the Dashboard

Once all services are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | Main web interface |
| **API** | http://localhost:8000 | Backend REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API docs |

### Default Login Credentials

```
Email:    admin@example.com
Password: changeme123
```

**⚠️ Change these immediately in production!**

---

## Development Workflow

### Making Backend Changes

The backend uses **hot-reload** in development. When you edit Python files:

1. Edit files in `backend/app/`
2. Save the file
3. The server automatically restarts
4. Check logs: `docker compose logs -f backend`

### Making Frontend Changes

For frontend development with hot-reload:

**Option A: Run frontend outside Docker (Recommended for development)**
```powershell
# Stop the Docker frontend
docker compose stop frontend

# Navigate to frontend folder
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Access at http://localhost:5173 (Vite's default port)

**Option B: Rebuild Docker container**
```powershell
docker compose up -d --build frontend
```

### Common Commands

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `docker compose down` | Stop all services |
| `docker compose restart` | Restart all services |
| `docker compose restart backend` | Restart just backend |
| `docker compose logs -f` | View live logs |
| `docker compose ps` | Check service status |
| `docker compose build` | Rebuild images |

---

## Troubleshooting

### Issue: "docker: command not found"

**Cause:** Docker is not installed or not in PATH

**Solution:**
1. Ensure Docker Desktop is installed
2. Restart your terminal/PowerShell
3. On Windows, restart your computer after Docker installation

### Issue: "Port already in use"

**Cause:** Another application is using port 3000, 8000, 5432, or 6379

**Solution:**
```powershell
# Find what's using the port (example: port 3000)
netstat -ano | findstr :3000

# Or change ports in docker-compose.yml
# Change "3000:80" to "3001:80" for example
```

### Issue: "Cannot connect to Docker daemon"

**Cause:** Docker Desktop is not running

**Solution:**
1. Open Docker Desktop application
2. Wait for it to fully start (check system tray icon)
3. Try the command again

### Issue: Database connection errors

**Cause:** Database container not ready yet

**Solution:**
```powershell
# Check if database is healthy
docker compose ps

# If not healthy, restart it
docker compose restart db

# Wait 30 seconds, then restart backend
docker compose restart backend
```

### Issue: Frontend shows blank page

**Cause:** Build failed or JavaScript errors

**Solution:**
```powershell
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose up -d --build frontend
```

### Issue: Changes not reflecting

**Cause:** Docker cache

**Solution:**
```powershell
# Rebuild without cache
docker compose build --no-cache
docker compose up -d
```

### Reset Everything

If all else fails, start fresh:

```powershell
# Stop and remove everything
docker compose down -v

# Remove all images (optional, will re-download everything)
docker system prune -a

# Start fresh
docker compose up -d --build
```

---

## Next Steps

Once running locally:

1. **Login** with default credentials
2. **Change the admin password** 
3. **Explore the API** at http://localhost:8000/docs
4. **Test Grafana integration** by sending a test webhook
5. **Read the file documentation** in `docs/file-explanation.md`

---

## Testing Grafana Webhook

You can test the webhook without Grafana using curl or PowerShell:

**PowerShell:**
```powershell
$body = @{
    status = "firing"
    alerts = @(
        @{
            status = "firing"
            labels = @{
                alertname = "TestAlert"
                severity = "critical"
            }
            annotations = @{
                summary = "This is a test alert"
                description = "Testing the Alert Dashboard webhook"
            }
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/webhooks/grafana" `
    -Method Post `
    -Headers @{"X-API-Key" = "your-webhook-api-key-change-in-production"; "Content-Type" = "application/json"} `
    -Body $body
```

After running this, you should see the alert appear in the dashboard!
