# VirtualBox Deployment Guide

This guide will help you deploy the Alert Dashboard on a VirtualBox VM.

## Prerequisites

- VirtualBox installed on your host machine
- At least 4GB RAM and 20GB disk space for the VM
- Internet connection for downloading packages

## Step 1: Create the Virtual Machine

1. **Download Ubuntu Server ISO**
   - Download Ubuntu Server 22.04 LTS from: https://ubuntu.com/download/server
   
2. **Create a new VM in VirtualBox**
   - Name: `alert-dashboard`
   - Type: Linux
   - Version: Ubuntu (64-bit)
   - Memory: 4096 MB (minimum 2048 MB)
   - Hard disk: Create a virtual hard disk now (VDI, dynamically allocated, 20GB)

3. **Configure VM Settings**
   - **Network**: Change from NAT to Bridged Adapter (to get an IP on your local network)
   - **Port Forwarding** (if using NAT):
     - Host Port 8080 → Guest Port 80 (HTTP)
     - Host Port 8443 → Guest Port 443 (HTTPS)
     - Host Port 2222 → Guest Port 22 (SSH)

4. **Install Ubuntu Server**
   - Mount the Ubuntu ISO and start the VM
   - Follow the installation wizard
   - Install OpenSSH server when prompted
   - Note down the username and password you create

## Step 2: Initial Server Setup

After Ubuntu installation, SSH into your VM:

```bash
# If using bridged networking, find the VM's IP with:
# (run this inside the VM)
ip addr show

# Then from your host machine:
ssh your-username@vm-ip-address
```

### Update System and Install Dependencies

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git
```

### Install Docker

```bash
# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin - Stopped here

# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in for the group change to take effect
exit
```

Log back in via SSH, then verify Docker installation:

```bash
docker --version
docker compose version
```

## Step 3: Deploy the Application

### Clone or Copy the Project

**Option A: Clone from Git (if you have a repo)**
```bash
git clone https://github.com/your-repo/alert-dashboard.git
cd alert-dashboard
```

**Option B: Copy files from host machine**
```bash
# From your host machine, copy files using scp:
scp -r "/path/to/Alert Dashboard" your-username@vm-ip:~/alert-dashboard
```

### Configure Environment Variables

```bash
cd ~/alert-dashboard

# Create production environment file
cat > .env << 'EOF'
# Database
DB_USER=alertuser
DB_PASSWORD=your-secure-password-here
DB_NAME=alertdb

# Security - CHANGE THESE!
SECRET_KEY=your-very-long-random-secret-key-at-least-32-chars
JWT_SECRET_KEY=another-very-long-random-secret-key-at-least-32-chars
API_KEY=your-webhook-api-key-for-grafana

# CORS - Update with your actual domain/IP
CORS_ORIGINS=["http://your-vm-ip","http://localhost"]

# Slack notifications (optional)
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=

# Email notifications (optional)
EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EOF
```

Generate secure keys:
```bash
# Generate random keys
openssl rand -hex 32  # Use output for SECRET_KEY
openssl rand -hex 32  # Use output for JWT_SECRET_KEY
openssl rand -hex 16  # Use output for API_KEY
```

### Build and Start the Application

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Check that all containers are running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

## Step 4: Access the Dashboard

1. Find your VM's IP address:
   ```bash
   ip addr show | grep inet
   ```

2. Open a browser and navigate to:
   - `http://your-vm-ip` (if using bridged networking)
   - `http://localhost:8080` (if using NAT with port forwarding)

3. Login with default credentials:
   - Email: `admin@example.com`
   - Password: `changeme123`

4. **IMPORTANT**: Change the default password immediately!

## Step 5: Configure Grafana Integration

In your Grafana instance:

1. Go to **Alerting → Contact Points**
2. Click **Add contact point**
3. Configure:
   - **Name**: Alert Dashboard
   - **Type**: Webhook
   - **URL**: `http://your-vm-ip/api/v1/webhooks/grafana`
   - **HTTP Method**: POST
   - Add header:
     - **Name**: `X-API-Key`
     - **Value**: Your API_KEY from the .env file

4. Test the contact point
5. Create notification policies that use this contact point

## Maintenance Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Update and restart
git pull  # if using git
docker compose -f docker-compose.prod.yml up -d --build

# Backup database
docker compose -f docker-compose.prod.yml exec db pg_dump -U alertuser alertdb > backup.sql

# Restore database
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U alertuser alertdb
```

## Troubleshooting

### Container won't start
```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs backend

# Check if ports are in use
sudo netstat -tlpn | grep -E '80|443|5432|6379'
```

### Database connection issues
```bash
# Check if database is running
docker compose -f docker-compose.prod.yml exec db psql -U alertuser -d alertdb -c '\l'
```

### Can't access from browser
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check if services are listening
curl http://localhost/health
```

## Security Recommendations

1. **Change default credentials** immediately after first login
2. **Use strong passwords** for all services
3. **Enable HTTPS** with Let's Encrypt for production
4. **Configure firewall** to only allow necessary ports
5. **Regular updates**: Keep the system and Docker images updated
6. **Backup regularly**: Set up automated database backups
