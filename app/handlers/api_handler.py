"""Lambda entry point for API Gateway — wraps FastAPI with Mangum."""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
