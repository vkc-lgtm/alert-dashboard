#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Alert Dashboard - Quick Start${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists for backend
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Creating backend .env file from example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${GREEN}Created backend/.env${NC}"
fi

# Check if .env file exists for frontend
if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}Creating frontend .env file from example...${NC}"
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}Created frontend/.env${NC}"
fi

echo -e "\n${YELLOW}Starting services with Docker Compose...${NC}\n"

# Start services
docker compose up -d --build

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   Services started successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "\n${GREEN}Access the application:${NC}"
    echo -e "  - Frontend:  ${YELLOW}http://localhost:3000${NC}"
    echo -e "  - Backend:   ${YELLOW}http://localhost:8000${NC}"
    echo -e "  - API Docs:  ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "\n${GREEN}Default credentials:${NC}"
    echo -e "  - Email:    ${YELLOW}admin@example.com${NC}"
    echo -e "  - Password: ${YELLOW}changeme123${NC}"
    echo -e "\n${GREEN}Useful commands:${NC}"
    echo -e "  - View logs:     ${YELLOW}docker compose logs -f${NC}"
    echo -e "  - Stop services: ${YELLOW}docker compose down${NC}"
    echo -e "  - Restart:       ${YELLOW}docker compose restart${NC}"
else
    echo -e "\n${RED}Failed to start services. Check the logs above for errors.${NC}"
    exit 1
fi
