# Async Starter - High-Performance FastAPI Application

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, high-performance asynchronous web application built with FastAPI, SQLAlchemy 2.0, and modern Python best practices. Designed for deployment on Google Kubernetes Engine (GKE) with full containerization support.

## Features

- **Modern Tech Stack**: FastAPI + SQLAlchemy 2.0 + Pydantic v2
- **Fully Asynchronous**: Built on Python's asyncio for maximum performance
- **Production-Ready**: Comprehensive error handling, logging, and monitoring
- **Container-First**: Optimized Docker images with multi-stage builds
- **GKE Optimized**: Kubernetes manifests with auto-scaling and health checks
- **Type-Safe**: Full type annotations with Python 3.11+ features
- **High-Performance**: Connection pooling, rate limiting, and caching support

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Testing](#testing)
- [Performance](#performance)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Architecture

```
async-starter/
├── src/                     # Main application source code
│   ├── app.py              # FastAPI application entry point
│   ├── config.py           # Pydantic-based configuration
│   ├── database.py         # Database connection management
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── middleware.py       # Custom middleware (logging, rate limiting)
│   ├── models.py           # SQLAlchemy 2.0 models
│   ├── repositories.py     # Data access layer
│   ├── schemas.py          # Pydantic v2 schemas
│   ├── routers/            # API route handlers
│   │   ├── health.py       # Health check endpoints
│   │   └── users.py        # User management endpoints
│   └── services/           # Business logic layer
│       └── user_service.py # User-related business logic
├── tests/                  # Comprehensive test suite
├── kubernetes.yaml         # K8s deployment manifests
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Local development environment
├── deploy-gke.sh          # GKE deployment script
├── run.py                 # Application entry point
└── README.md              # This file
```

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | MySQL | 8.0 |
| Validation | Pydantic | v2 |
| ASGI Server | Uvicorn | 0.34+ |
| Package Manager | uv | Latest |
| Container | Docker | 20.10+ |
| Orchestration | Kubernetes | 1.28+ |

## Prerequisites

### Required Software

- Python 3.11 or higher
- Docker & Docker Compose
- Google Cloud SDK (for GKE deployment)
- kubectl (for Kubernetes management)

### Optional Tools

- uv (recommended Python package manager)
- Make (for automation)
- k9s (Kubernetes CLI UI)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/async-starter.git
cd async-starter
```

### 2. Set Up Environment

```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
# Especially database credentials
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f app

# Access the application
open http://localhost:8000
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Local Development Setup

```bash
# Install uv (fast Python package manager)
pip install uv

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Run development server
python run.py
```

### Development Features

- **Hot Reload**: Automatic restart on code changes
- **Debug Mode**: Detailed error messages and stack traces
- **Interactive API Docs**: Built-in Swagger UI
- **Database Migrations**: Automatic table creation in dev mode

### Code Style

This project follows:
- [PEP 8](https://pep8.org/) style guide
- [Black](https://github.com/psf/black) code formatter
- [isort](https://pycqa.github.io/isort/) import sorting
- Type hints throughout the codebase

## API Documentation

### Available Endpoints

#### Health Check
- `GET /health` - Application health status

#### User Management
- `GET /api/v1/users` - List users (paginated)
- `GET /api/v1/users/{user_id}` - Get specific user
- `POST /api/v1/users` - Create new user
- `PATCH /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Request/Response Examples

#### Create User
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

#### List Users with Pagination
```bash
curl "http://localhost:8000/api/v1/users?page=1&per_page=20"
```

## Deployment

### Google Kubernetes Engine (GKE)

#### Automated Deployment

```bash
# Deploy to GKE with single command
./deploy-gke.sh -p YOUR_PROJECT_ID
```

#### Manual Deployment

1. **Build and Push Docker Image**
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/async-starter:latest .
docker push gcr.io/YOUR_PROJECT_ID/async-starter:latest
```

2. **Create GKE Cluster**
```bash
gcloud container clusters create async-starter-cluster \
  --zone=asia-northeast1-a \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

3. **Deploy Application**
```bash
kubectl apply -f kubernetes.yaml
```

### Docker Image

The Dockerfile uses multi-stage builds for optimization:
- **Build Stage**: Installs dependencies
- **Runtime Stage**: Minimal production image
- **Security**: Runs as non-root user
- **Size**: ~150MB final image

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `true` | Debug mode flag |
| `LOG_LEVEL` | `info` | Logging level |
| `PORT` | `8000` | Application port |
| `WORKERS` | `4` | Number of worker processes |
| **Database** | | |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `3306` | Database port |
| `DB_USER` | `testuser` | Database username |
| `DB_PASSWORD` | `testpass` | Database password |
| `DB_NAME` | `testdb` | Database name |
| **Connection Pool** | | |
| `DB_POOL_MIN_SIZE` | `5` | Minimum connections |
| `DB_POOL_MAX_SIZE` | `20` | Maximum connections |
| `DB_POOL_RECYCLE` | `3600` | Connection recycle time |

### Configuration Management

Configuration is managed through Pydantic Settings:
- Type validation
- Environment variable loading
- Nested configuration support
- Computed properties

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

### Test Structure

- `test_api.py` - API endpoint tests
- `test_models.py` - Database model tests
- `test_repositories.py` - Data access tests
- `test_services.py` - Business logic tests
- `test_config.py` - Configuration tests

## Performance

### Optimization Features

1. **Connection Pooling**
   - Configurable pool size
   - Connection recycling
   - Overflow handling

2. **Async Processing**
   - Non-blocking I/O
   - Concurrent request handling
   - Efficient database queries

3. **Caching Support**
   - Redis integration ready
   - Query result caching
   - Session caching

4. **Rate Limiting**
   - Per-IP rate limiting
   - Configurable limits
   - DDoS protection

### Benchmarks

```bash
# Example load test with Apache Bench
ab -n 10000 -c 100 http://localhost:8000/api/v1/users
```

Expected performance:
- Requests per second: 5000+ (depends on hardware)
- Average response time: <50ms
- Concurrent connections: 1000+

## Security

### Security Features

- **Authentication Ready**: JWT token support structure
- **Input Validation**: Pydantic schemas with strict validation
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **Rate Limiting**: Built-in DDoS protection
- **CORS Configuration**: Configurable origin control
- **Non-root Container**: Security-hardened Docker image

### Security Best Practices

1. Always use environment variables for secrets
2. Enable HTTPS in production
3. Regularly update dependencies
4. Use least-privilege database users
5. Enable audit logging

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Write tests for new features
- Update documentation
- Follow existing code style
- Add type hints
- Include docstrings

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

## Support

- Documentation: [Project Wiki](https://github.com/yourusername/async-starter/wiki)
- Issues: [GitHub Issues](https://github.com/yourusername/async-starter/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/async-starter/discussions)

---

Built with ♥ using Python and FastAPI
