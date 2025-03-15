# Urban Lens API

A FastAPI-based backend for the Urban Lens application, providing user management and data services.

## Features

- User authentication and management
- RESTful API with automatic documentation
- Async PostgreSQL database integration
- Secure password handling

## Tech Stack

- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: ORM for database interactions
- **PostgreSQL**: Database for data storage
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization for development and deployment

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL (or Docker for containerized setup)
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd urban-lens-api
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env` (if not already present)
   - Update the environment variables with your configuration

5. Run the PostgreSQL database:
   ```bash
   docker-compose up -d
   ```

6. Start the application:
   ```bash
   uvicorn main:app --reload
   ```

7. Visit API documentation at [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

## Development

### Database Migrations

This project uses Alembic for database migrations:

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

### Testing

Run tests with pytest:

```bash
pytest
```

## API Documentation

When the application is running, you can access:

- Swagger UI: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- ReDoc: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

## Deployment

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t urban-lens-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 urban-lens-api
   ```

## License

[Add license information here] 