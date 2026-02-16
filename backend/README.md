# EquiVision Backend Service

This is the FastAPI backend for the EquiVision application. It provides authentication, price estimation, and breed classification services.

## Prerequisites
- Python 3.11+
- Docker Desktop (for PostgreSQL and Breed Classification ML Service)

## Quick Start (Windows)

1. **Start Docker Desktop**: Ensure Docker is running.
2. **Run the Startup Script**:
   ```bash
   start_server.bat
   ```
   This script will automatically:
   - Verify Docker availability
   - Start the PostgreSQL database container (`equivision-db`) on port 5433
   - Start the ML Proxy container (`equivision-ml-backend`) on port 8001 (required for Windows compatibility)
   - Start the local API server on http://localhost:8000

## Verification

To verify that all services are running correctly, run:
```bash
python final_check.py
```

## API Endpoints

- **Authentication**:
  - `POST /auth/register`: Register new user
  - `POST /auth/login`: Login user (returns JWT token)
  - `GET /auth/me`: Get current user info (requires Bearer token)

- **ML Services**:
  - `POST /predict/breed`: Upload image to predict horse breed (Proxied to Docker)
  - `POST /predict/price`: Estimate horse price based on attributes (Local Model)
  - `POST /predict/complete`: Combined prediction (Image + Attributes)

## Development Notes

### Windows Compatibility
The Breed Classification service uses specific ML libraries that may have compatibility issues on Windows (e.g., NumPy DLL errors). To resolve this, a "Smart Proxy" pattern is implemented:
- The local API handles authentication and pricing logic.
- Breed classification requests are automatically forwarded to a Linux-based Docker container (`equivision-ml-backend`) running on port 8001.
- If the Docker container is not available, the service will degrade gracefully (Vision features disabled).

### Docker Commands
If you need to manage containers manually:

**Database:**
```bash
docker run -d --name equivision-db -e POSTGRES_PASSWORD=equivision123 -e POSTGRES_DB=equivision_db -p 5433:5432 postgres:15
```

**ML Backend:**
```bash
docker run -d -p 8001:8000 --name equivision-ml-backend -e ML_MODE=VISION_ONLY -v "%cd%":/app equivision-backend-serve
```
