# Alert Dashboard

A self-hosted alert management system similar to OpsGenie/PagerDuty, designed to receive alerts from Grafana and other monitoring tools.

## Features

- ✅ Receive alerts via webhooks (Grafana compatible)
- ✅ Alert acknowledgment/resolution workflow
- ✅ Severity levels (Critical, Warning, Info)
- ✅ Alert grouping and deduplication
- ✅ Email notifications
- ✅ Slack notifications
- ✅ User authentication with roles (Admin, User, Viewer)
- ✅ Alert history and reporting
- ✅ Real-time dashboard updates via WebSockets
- ✅ RESTful API

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React with TypeScript
- **Database:** PostgreSQL
- **Cache/Queue:** Redis
- **Containerization:** Docker & Docker Compose

## Project Structure

```
alert-dashboard/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, dependencies
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry point
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React application
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## Quick Start

### Development (Local)

1. Clone the repository
2. Copy environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
3. Start services:
   ```bash
   docker-compose up -d
   ```
4. Access the dashboard at http://localhost:3000

### Production (VirtualBox VM)

See [docs/deployment-virtualbox.md](docs/deployment-virtualbox.md)

### AWS Deployment

See [docs/deployment-aws.md](docs/deployment-aws.md)

## Grafana Integration

1. In Grafana, go to Alerting > Contact Points
2. Add a new contact point with type "Webhook"
3. Set URL to: `http://your-server:8000/api/v1/webhooks/grafana`
4. Add header: `X-API-Key: your-api-key`

## API Documentation

Once running, access the API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Credentials

- **Admin User:** admin@example.com / changeme123

## License

MIT
