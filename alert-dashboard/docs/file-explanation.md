# File Structure Explanation

This document explains every file in the Alert Dashboard project, organized by purpose.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Root Directory Files](#root-directory-files)
3. [Backend (Python/FastAPI)](#backend-pythonfastapi)
4. [Frontend (React/TypeScript)](#frontend-reacttypescript)
5. [Documentation](#documentation)

---

## Project Overview

```
Alert Dashboard/
├── backend/                 # Python FastAPI application (REST API)
│   ├── app/                # Application code
│   │   ├── api/           # HTTP route handlers
│   │   ├── core/          # Configuration, security, database
│   │   ├── models/        # Database table definitions
│   │   ├── schemas/       # Data validation schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # Application entry point
│   ├── Dockerfile         # Container build instructions
│   └── requirements.txt   # Python dependencies
│
├── frontend/               # React TypeScript application (Web UI)
│   ├── src/               # Source code
│   │   ├── api/          # API call functions
│   │   ├── components/   # Reusable UI components
│   │   ├── hooks/        # React custom hooks
│   │   ├── pages/        # Page components
│   │   ├── store/        # State management
│   │   ├── types/        # TypeScript type definitions
│   │   └── App.tsx       # Main application component
│   ├── Dockerfile        # Container build instructions
│   └── package.json      # Node.js dependencies
│
├── docs/                   # Documentation
├── docker-compose.yml      # Development container setup
├── docker-compose.prod.yml # Production container setup
└── README.md              # Project overview
```

---

## Root Directory Files

### `README.md`
**Purpose:** Project overview and quick-start guide  
**Who uses it:** Anyone new to the project

```markdown
# What it contains:
- Feature list
- Tech stack overview
- Quick start instructions
- Default credentials
```

### `docker-compose.yml`
**Purpose:** Defines all services needed to run the app locally  
**Who uses it:** Docker Compose reads this to start containers

```yaml
# Key sections explained:

version: '3.8'                    # Docker Compose file format version

services:                         # Each service becomes a container
  db:                            # PostgreSQL database
    image: postgres:15-alpine    # Use official PostgreSQL image
    environment:                 # Database credentials
      POSTGRES_USER: alertuser
      POSTGRES_PASSWORD: alertpass
    volumes:                     # Persist data between restarts
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"             # host_port:container_port
    healthcheck:                # Docker checks if DB is ready
      test: ["CMD-SHELL", "pg_isready"]

  redis:                        # Redis cache/message queue
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:                      # Our Python API
    build: ./backend            # Build from backend/Dockerfile
    environment:                # Environment variables
      - DATABASE_URL=postgresql+asyncpg://alertuser:alertpass@db:5432/alertdb
    ports:
      - "8000:8000"
    depends_on:                 # Start after db and redis
      db:
        condition: service_healthy

  frontend:                     # Our React app
    build: ./frontend
    ports:
      - "3000:80"              # Access on localhost:3000
    depends_on:
      - backend

volumes:                        # Named volumes for data persistence
  postgres_data:               # Database files survive container restart
  redis_data:
```

### `docker-compose.prod.yml`
**Purpose:** Production configuration with security and networking  
**Differences from dev:**
- Uses environment variables for secrets (not hardcoded)
- Creates isolated network
- No port exposure for database (security)
- Restart policies

### `.gitignore`
**Purpose:** Tells Git which files NOT to track  
**Why it matters:** Prevents sensitive data and generated files from being committed

```
# Examples of ignored files:
.env              # Contains secrets
node_modules/     # Dependencies (reinstalled via npm)
__pycache__/      # Python compiled files
*.pyc             # Python bytecode
.DS_Store         # Mac system files
```

### `start.sh`
**Purpose:** Quick start script for Mac/Linux  
**What it does:**
1. Checks if Docker is installed
2. Creates .env files if missing
3. Runs docker-compose
4. Prints access URLs

---

## Backend (Python/FastAPI)

The backend is built with **FastAPI**, a modern Python web framework that's:
- Fast to code
- Fast to run
- Automatic API documentation
- Built-in data validation

### `backend/requirements.txt`
**Purpose:** Lists all Python packages the project needs

```txt
# Web framework
fastapi==0.109.0          # The web framework itself
uvicorn[standard]==0.27.0 # ASGI server (runs FastAPI)

# Database
sqlalchemy==2.0.25        # ORM (maps Python objects to database tables)
asyncpg==0.29.0          # PostgreSQL driver (async)
alembic==1.13.1          # Database migrations

# Authentication
python-jose==3.3.0       # JWT token handling
passlib==1.7.4           # Password hashing
bcrypt==4.1.2            # Encryption algorithm

# Validation
pydantic==2.5.3          # Data validation (used by FastAPI)
email-validator==2.1.0   # Validates email addresses

# HTTP client (for sending Slack notifications)
httpx==0.26.0            # Async HTTP client
```

### `backend/Dockerfile`
**Purpose:** Instructions to build the backend container

```dockerfile
FROM python:3.11-slim     # Start with Python 3.11 base image

WORKDIR /app              # Set working directory in container

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \                 # C compiler (needed for some Python packages)
    libpq-dev            # PostgreSQL development files

COPY requirements.txt .   # Copy requirements first
RUN pip install -r requirements.txt  # Install Python packages

COPY . .                  # Copy all backend code

EXPOSE 8000               # Document that this container uses port 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# ^ Start the FastAPI application
```

### `backend/.env.example`
**Purpose:** Template for environment variables  
**How to use:** Copy to `.env` and fill in your values

```env
# Application settings
APP_NAME=Alert Dashboard
DEBUG=true                    # Enable detailed errors (disable in production!)

# Security keys - CHANGE THESE IN PRODUCTION
SECRET_KEY=your-secret        # For general encryption
JWT_SECRET_KEY=jwt-secret     # For user authentication tokens
API_KEY=webhook-api-key       # For Grafana webhook authentication

# Database connection string
# Format: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
DATABASE_URL=postgresql+asyncpg://alertuser:alertpass@db:5432/alertdb

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SLACK_ENABLED=false
```

---

### `backend/app/` - Application Code

#### `backend/app/main.py`
**Purpose:** Application entry point - where FastAPI starts

```python
# Key concepts explained:

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Lifespan: Code that runs when app starts/stops
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Runs once when application starts
    print("Starting Alert Dashboard...")
    await init_db()  # Create database tables
    
    # Create default admin user if none exists
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        await user_service.create_default_admin()
    
    yield  # Application runs here
    
    # SHUTDOWN: Runs when application stops
    print("Shutting down...")

# Create the FastAPI application
app = FastAPI(
    title="Alert Dashboard",
    docs_url="/docs",     # Swagger UI at /docs
    redoc_url="/redoc",   # ReDoc at /redoc
    lifespan=lifespan
)

# CORS: Allow frontend to make requests to backend
# Without this, browser blocks requests from localhost:3000 to localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router)

# Health check endpoint - useful for monitoring
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Handles real-time communication with frontend
    await manager.connect(websocket)
    ...
```

#### `backend/app/core/config.py`
**Purpose:** Application configuration from environment variables

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Pydantic automatically reads from environment variables!
    
    If you have DATABASE_URL in .env or system environment,
    it automatically populates settings.DATABASE_URL
    """
    
    # Application settings
    APP_NAME: str = "Alert Dashboard"  # Default value if not in env
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://..."
    
    # Security
    SECRET_KEY: str = "change-me"
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"  # Load from .env file

# Create a single instance used throughout the app
settings = Settings()

# Usage elsewhere: from app.core.config import settings
# Then: settings.DATABASE_URL
```

#### `backend/app/core/security.py`
**Purpose:** Password hashing and JWT token functions

```python
from passlib.context import CryptContext
from jose import jwt

# Password hashing using bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"])

def get_password_hash(password: str) -> str:
    """
    Convert plain password to hash.
    Example: "mypassword" -> "$2b$12$xyz..."
    
    Why hash? If database is stolen, passwords aren't readable
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if password matches the hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Create a JWT (JSON Web Token) for authentication.
    
    JWT contains:
    - User ID (so we know who's making requests)
    - Expiration time (tokens expire after 30 minutes)
    - Signature (proves token wasn't tampered with)
    
    Frontend stores this and sends it with every request
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
```

#### `backend/app/core/database.py`
**Purpose:** Database connection setup

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Create database engine (connection pool)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,     # Print SQL queries in debug mode
    pool_size=10,            # Keep 10 connections ready
)

# Session factory - creates database sessions
AsyncSessionLocal = async_sessionmaker(engine)

# Base class for all database models
Base = declarative_base()

# Dependency for FastAPI routes
async def get_db() -> AsyncSession:
    """
    Creates a database session for each request.
    
    Usage in routes:
    @router.get("/alerts")
    async def get_alerts(db: AsyncSession = Depends(get_db)):
        # db is now a database session
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Save changes
        except Exception:
            await session.rollback()  # Undo on error
```

---

### `backend/app/models/` - Database Models

These define your database tables using SQLAlchemy ORM.

#### `backend/app/models/alert.py`
**Purpose:** Define the alerts table structure

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.core.database import Base
import enum

# Python enums become database ENUM types
class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(str, enum.Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alert(Base):
    """
    This class becomes a database table called "alerts"
    
    Each attribute becomes a column:
    - id: Primary key, auto-incremented
    - title: Text up to 500 characters
    - severity: One of critical/warning/info
    - etc.
    """
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(255), index=True)  # For deduplication
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)
    status = Column(Enum(AlertStatus), default=AlertStatus.FIRING)
    source = Column(String(100), default="grafana")
    
    # Timestamps
    fired_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Foreign keys - link to users table
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships - SQLAlchemy loads related objects
    acknowledged_by = relationship("User")
    history = relationship("AlertHistory", back_populates="alert")

# This creates SQL like:
# CREATE TABLE alerts (
#     id SERIAL PRIMARY KEY,
#     fingerprint VARCHAR(255),
#     title VARCHAR(500) NOT NULL,
#     ...
# );
```

#### `backend/app/models/user.py`
**Purpose:** Define the users table

```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"      # Can manage users, change settings
    USER = "user"        # Can acknowledge/resolve alerts
    VIEWER = "viewer"    # Can only view alerts

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)  # unique=True prevents duplicates
    hashed_password = Column(String(255))  # Never store plain passwords!
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    slack_notifications = Column(Boolean, default=True)
```

---

### `backend/app/schemas/` - Pydantic Schemas

Schemas define what data looks like going in and out of the API.

#### `backend/app/schemas/alert.py`
**Purpose:** Validate and serialize alert data

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema for CREATING an alert (input)
class AlertCreate(BaseModel):
    """
    When someone creates an alert, they must provide this data.
    Pydantic validates it automatically!
    """
    title: str = Field(..., max_length=500)  # ... means required
    description: Optional[str] = None         # Optional field
    severity: AlertSeverity = AlertSeverity.WARNING  # Default value

# Schema for READING an alert (output)
class AlertResponse(BaseModel):
    """
    When API returns an alert, it includes all these fields.
    """
    id: int
    fingerprint: str
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    fired_at: datetime
    acknowledged_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model

# Example API usage:
# POST /alerts with body {"title": "Server Down", "severity": "critical"}
# Returns: {"id": 1, "title": "Server Down", "severity": "critical", ...}
```

---

### `backend/app/services/` - Business Logic

Services contain the actual logic, separate from HTTP handling.

#### `backend/app/services/alert_service.py`
**Purpose:** All alert-related operations

```python
class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        """
        Create a new alert with deduplication.
        
        Deduplication: If same alert fires within 5 minutes,
        don't create duplicate - just update timestamp.
        """
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(alert_data.title, alert_data.labels)
        
        # Check if similar alert exists
        existing = await self.get_active_alert_by_fingerprint(fingerprint)
        if existing:
            # Update existing instead of creating new
            existing.updated_at = datetime.utcnow()
            return existing
        
        # Create new alert
        alert = Alert(
            fingerprint=fingerprint,
            title=alert_data.title,
            severity=alert_data.severity,
            status=AlertStatus.FIRING,
        )
        self.db.add(alert)
        await self.db.commit()
        return alert
    
    async def acknowledge_alert(self, alert_id: int, user: User) -> Alert:
        """Mark an alert as acknowledged by a user"""
        alert = await self.get_alert_by_id(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by_id = user.id
        await self.db.commit()
        return alert
```

#### `backend/app/services/notification_service.py`
**Purpose:** Send notifications to Slack and Email

```python
class NotificationService:
    async def send_slack_notification(self, alert: Alert, action: str) -> bool:
        """
        Send alert to Slack channel via webhook.
        
        Slack webhooks: You create a webhook URL in Slack,
        then POST JSON to it, and Slack shows the message.
        """
        if not settings.SLACK_ENABLED:
            return False
        
        # Build Slack message format
        message = {
            "attachments": [{
                "color": "#dc3545" if alert.severity == "critical" else "#ffc107",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{alert.title}*\nSeverity: {alert.severity}"
                        }
                    }
                ]
            }]
        }
        
        # Send to Slack
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.SLACK_WEBHOOK_URL, json=message)
            return response.status_code == 200
```

---

### `backend/app/api/` - HTTP Routes

Routes define the API endpoints.

#### `backend/app/api/routes/alerts.py`
**Purpose:** Alert CRUD endpoints

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[AlertStatus] = Query(None),  # Query parameter: /alerts?status=firing
    page: int = Query(1, ge=1),                    # Pagination
    db: AsyncSession = Depends(get_db),            # Database injection
    current_user: User = Depends(require_any_role) # Auth required
):
    """
    GET /api/v1/alerts
    
    Returns paginated list of alerts.
    Optional filters: status, severity, search
    """
    alert_service = AlertService(db)
    alerts, total = await alert_service.get_alerts(
        status=status,
        page=page
    )
    return AlertListResponse(alerts=alerts, total=total, page=page)

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,                                  # Path parameter
    ack_data: AlertAcknowledge,                     # Request body
    current_user: User = Depends(require_user_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /api/v1/alerts/123/acknowledge
    
    Marks alert as acknowledged by current user.
    """
    alert_service = AlertService(db)
    alert = await alert_service.acknowledge_alert(alert_id, current_user)
    
    # Send notification
    await notification_service.send_slack_notification(alert, "acknowledged")
    
    return alert
```

#### `backend/app/api/routes/webhooks.py`
**Purpose:** Receive alerts from Grafana

```python
@router.post("/grafana")
async def grafana_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)  # Requires X-API-Key header
):
    """
    POST /api/v1/webhooks/grafana
    
    Grafana sends alerts here. We parse them and create
    alerts in our system.
    
    Grafana payload example:
    {
        "status": "firing",
        "alerts": [
            {
                "labels": {"alertname": "HighCPU", "severity": "warning"},
                "annotations": {"summary": "CPU > 80%"}
            }
        ]
    }
    """
    body = await request.json()
    alert_service = AlertService(db)
    
    for grafana_alert in body.get("alerts", []):
        if grafana_alert["status"] == "firing":
            # Create alert in our system
            alert = await alert_service.create_alert(...)
            await notification_service.send_slack_notification(alert, "fired")
        elif grafana_alert["status"] == "resolved":
            # Resolve existing alert
            await alert_service.resolve_alert_by_fingerprint(...)
    
    return {"status": "ok"}
```

#### `backend/app/api/dependencies.py`
**Purpose:** Reusable authentication logic

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extracts and validates JWT token from request.
    
    Usage:
    @router.get("/something")
    async def something(user: User = Depends(get_current_user)):
        # user is the authenticated user
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await user_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Role-based access
def require_role(allowed_roles: list[UserRole]):
    """Create a dependency that requires specific roles"""
    async def checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker

require_admin = require_role([UserRole.ADMIN])
require_user_or_admin = require_role([UserRole.ADMIN, UserRole.USER])
```

---

## Frontend (React/TypeScript)

The frontend is built with **React** (UI library) and **TypeScript** (JavaScript with types).

### Key Concepts for Python Developers

| Python | TypeScript/React |
|--------|------------------|
| `class` | `interface` / `type` (for data shapes) |
| `def function():` | `function name() {}` or `const name = () => {}` |
| `import module` | `import { thing } from 'module'` |
| `dict` | `object` / `Record<string, any>` |
| `list` | `array` / `string[]` |
| `None` | `null` / `undefined` |

### `frontend/package.json`
**Purpose:** Node.js project configuration and dependencies

```json
{
  "name": "alert-dashboard-frontend",
  "scripts": {
    "dev": "vite",           // Start development server
    "build": "tsc && vite build",  // Build for production
    "preview": "vite preview" // Preview production build
  },
  "dependencies": {
    "react": "^18.2.0",           // UI library
    "react-dom": "^18.2.0",       // React for web browsers
    "react-router-dom": "^6.21.1", // Page routing
    "axios": "^1.6.5",            // HTTP client (like requests in Python)
    "@tanstack/react-query": "^5.17.9", // Data fetching & caching
    "zustand": "^4.4.7",          // State management
    "lucide-react": "^0.303.0",   // Icons
    "date-fns": "^3.2.0",         // Date formatting
    "clsx": "^2.1.0"              // CSS class utilities
  },
  "devDependencies": {
    "typescript": "^5.3.3",       // TypeScript compiler
    "vite": "^5.0.11",            // Build tool & dev server
    "tailwindcss": "^3.4.1"       // CSS framework
  }
}
```

### `frontend/src/types/index.ts`
**Purpose:** TypeScript type definitions (like Python type hints)

```typescript
// Define what an Alert looks like
// Similar to Python's TypedDict or @dataclass
export interface Alert {
  id: number;
  fingerprint: string;
  title: string;
  description: string | null;  // Can be string or null
  severity: 'critical' | 'warning' | 'info';  // Literal types
  status: 'firing' | 'acknowledged' | 'resolved';
  fired_at: string;  // ISO date string
  acknowledged_at: string | null;
}

// Define what the API returns for alert list
export interface AlertListResponse {
  alerts: Alert[];  // Array of Alert objects
  total: number;
  page: number;
  page_size: number;
}

// User type
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: 'admin' | 'user' | 'viewer';
}
```

### `frontend/src/lib/api.ts`
**Purpose:** Configure axios HTTP client

```typescript
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

// Create axios instance with base URL
export const api = axios.create({
  baseURL: '/api/v1',  // All requests go to /api/v1/...
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Runs before every request
// Adds authentication token automatically
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor: Runs after every response
// Handles token refresh if expired
api.interceptors.response.use(
  (response) => response,  // Success: return response
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      // ... refresh logic ...
    }
    return Promise.reject(error);
  }
);
```

### `frontend/src/api/alerts.ts`
**Purpose:** API functions for alerts

```typescript
import { api } from '../lib/api';
import { Alert, AlertListResponse, AlertStats } from '../types';

export const alertsApi = {
  // GET /api/v1/alerts
  getAlerts: async (params = {}): Promise<AlertListResponse> => {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  // GET /api/v1/alerts/123
  getAlert: async (id: number): Promise<Alert> => {
    const response = await api.get(`/alerts/${id}`);
    return response.data;
  },

  // POST /api/v1/alerts/123/acknowledge
  acknowledgeAlert: async (id: number, comment?: string): Promise<Alert> => {
    const response = await api.post(`/alerts/${id}/acknowledge`, { comment });
    return response.data;
  },
};
```

### `frontend/src/store/authStore.ts`
**Purpose:** Global authentication state

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Define the state shape
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// Create the store
// zustand is like a simpler Redux
export const useAuthStore = create<AuthState>()(
  persist(  // persist saves to localStorage
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        // Call API
        const response = await api.post('/auth/login', { email, password });
        const { access_token, refresh_token } = response.data;
        
        // Update state
        set({
          token: access_token,
          isAuthenticated: true,
        });
        
        // Fetch user info
        await get().fetchUser();
      },
      
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
      },
    }),
    { name: 'auth-storage' }  // localStorage key
  )
);

// Usage in components:
// const { user, login, logout } = useAuthStore();
```

### `frontend/src/hooks/useAlerts.ts`
**Purpose:** React hooks for fetching alerts

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi } from '../api/alerts';

// Hook to fetch alerts
export function useAlerts(params = {}) {
  return useQuery({
    queryKey: ['alerts', params],  // Cache key
    queryFn: () => alertsApi.getAlerts(params),  // How to fetch
    refetchInterval: 30000,  // Refetch every 30 seconds
  });
}

// Hook to acknowledge an alert
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, comment }) => alertsApi.acknowledgeAlert(id, comment),
    onSuccess: () => {
      // Refresh alerts list after acknowledging
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

// Usage in components:
// const { data: alerts, isLoading } = useAlerts();
// const acknowledgeMutation = useAcknowledgeAlert();
// acknowledgeMutation.mutate({ id: 123 });
```

### `frontend/src/components/alerts/AlertCard.tsx`
**Purpose:** Display a single alert

```tsx
import React from 'react';
import { Alert } from '../../types';
import { formatDistanceToNow } from 'date-fns';

// Props: What data this component needs
interface AlertCardProps {
  alert: Alert;
  onClick?: () => void;
  onAcknowledge?: () => void;
}

// Function component
export function AlertCard({ alert, onClick, onAcknowledge }: AlertCardProps) {
  return (
    <div 
      className="border rounded-lg p-4 cursor-pointer"
      onClick={onClick}
    >
      {/* Alert header */}
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${
          alert.status === 'firing' ? 'bg-red-500' :
          alert.status === 'acknowledged' ? 'bg-yellow-500' :
          'bg-green-500'
        }`} />
        <span className="text-xs uppercase">{alert.status}</span>
      </div>
      
      {/* Alert title */}
      <h3 className="font-semibold">{alert.title}</h3>
      
      {/* Time since fired */}
      <p className="text-xs text-gray-500">
        Fired {formatDistanceToNow(new Date(alert.fired_at), { addSuffix: true })}
      </p>
      
      {/* Action buttons */}
      {alert.status === 'firing' && onAcknowledge && (
        <button
          onClick={(e) => {
            e.stopPropagation();  // Don't trigger card click
            onAcknowledge();
          }}
          className="px-3 py-1 bg-yellow-500 text-white rounded"
        >
          Acknowledge
        </button>
      )}
    </div>
  );
}
```

### `frontend/src/pages/DashboardPage.tsx`
**Purpose:** Main dashboard page

```tsx
import { useState } from 'react';
import { useAlerts, useAcknowledgeAlert } from '../hooks/useAlerts';
import { AlertCard } from '../components/alerts/AlertCard';

export function DashboardPage() {
  // State for filters
  const [filters, setFilters] = useState({});
  
  // Fetch alerts using our hook
  const { data, isLoading } = useAlerts(filters);
  
  // Mutation for acknowledging
  const acknowledgeMutation = useAcknowledgeAlert();
  
  const handleAcknowledge = async (alertId: number) => {
    await acknowledgeMutation.mutateAsync({ id: alertId });
  };
  
  // Loading state
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  // Render alerts
  return (
    <div className="space-y-4">
      <h1>Alert Dashboard</h1>
      
      {data?.alerts.map((alert) => (
        <AlertCard
          key={alert.id}
          alert={alert}
          onAcknowledge={() => handleAcknowledge(alert.id)}
        />
      ))}
    </div>
  );
}
```

### `frontend/src/App.tsx`
**Purpose:** Main app with routing

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { useAuthStore } from './store/authStore';

// Protect routes that require auth
function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;  // Redirect to login
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
```

### `frontend/Dockerfile`
**Purpose:** Build frontend for production

```dockerfile
# Stage 1: Build
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci                    # Install dependencies
COPY . .
RUN npm run build            # Build production files

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### `frontend/nginx.conf`
**Purpose:** Web server configuration

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    
    # Serve React app
    location / {
        try_files $uri $uri/ /index.html;
        # ^ If file not found, serve index.html (for React Router)
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:8000;
    }
    
    # Proxy WebSocket
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Summary: Request Flow

Here's how a request flows through the system:

```
User clicks "Acknowledge" button
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                │
│                                                                 │
│ AlertCard.tsx                                                   │
│   └─> onAcknowledge()                                          │
│         └─> acknowledgeMutation.mutate({ id: 123 })            │
│                                                                 │
│ useAlerts.ts (React Query)                                      │
│   └─> alertsApi.acknowledgeAlert(123)                          │
│                                                                 │
│ api/alerts.ts                                                   │
│   └─> api.post('/alerts/123/acknowledge')                      │
│                                                                 │
│ lib/api.ts (Axios interceptor)                                  │
│   └─> Adds Authorization: Bearer <token>                       │
└─────────────────────────────────────────────────────────────────┘
         │
         │ HTTP POST /api/v1/alerts/123/acknowledge
         │ Headers: Authorization: Bearer eyJ...
         │ Body: { "comment": null }
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI)                                               │
│                                                                 │
│ api/routes/alerts.py                                            │
│   @router.post("/{alert_id}/acknowledge")                      │
│   └─> Depends(get_current_user) validates token                │
│   └─> Depends(get_db) creates database session                 │
│   └─> Calls alert_service.acknowledge_alert()                  │
│                                                                 │
│ services/alert_service.py                                       │
│   └─> Updates alert in database                                │
│   └─> Creates history record                                   │
│                                                                 │
│ services/notification_service.py                                │
│   └─> Sends Slack notification (if enabled)                    │
│                                                                 │
│ Returns AlertResponse (JSON)                                    │
└─────────────────────────────────────────────────────────────────┘
         │
         │ HTTP 200 OK
         │ Body: { "id": 123, "status": "acknowledged", ... }
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                │
│                                                                 │
│ React Query                                                     │
│   └─> onSuccess: invalidateQueries(['alerts'])                 │
│   └─> Triggers refetch of alerts list                          │
│                                                                 │
│ UI Updates automatically                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

This covers all the major files! The key concepts are:

1. **Backend**: FastAPI handles HTTP requests, SQLAlchemy manages the database, Pydantic validates data
2. **Frontend**: React renders UI, React Query fetches data, Zustand manages global state
3. **Docker**: Packages everything into containers that work identically everywhere
