import logging

from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from contextlib import asynccontextmanager
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from database import get_db, init_db
from api.users import router as users_router
from api.auth import router as auth_router
from api.locations import router as locations_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")

# Request processing time middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log requests that take too long
        if process_time > 0.5:  # Log slow requests (>500ms)
            logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")

        return response


# Add request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]

        # Log all incoming requests with more details
        logger.info(
            f"Request [{request_id}]: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate process time
            process_time = time.time() - start_time

            # Log the response status code and timing
            logger.info(
                f"Response [{request_id}]: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")

            return response
        except Exception as e:
            # Log exceptions during request processing
            logger.error(f"Request exception [{request_id}]: {request.method} {request.url.path} - Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # Re-raise to let FastAPI exception handlers deal with it




# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Urban Lens API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Include API routers
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(locations_router, prefix=settings.API_V1_STR)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    # Ensure localhost:3000 is included for frontend development
    if "http://localhost:3000" not in origins:
        origins.append("http://localhost:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # If no origins are configured, at least allow localhost:3000
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add timing middleware for performance monitoring
app.add_middleware(TimingMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)



# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "0.1.0",
    }


# Health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check():
    return {
        "status": "healthy",
        "api_version": "v1",
        "environment": "development" if settings.DEBUG else "production"
    }
