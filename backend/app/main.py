import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import account, admin, ai, auth, complaints, dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("civicpulse")

app = FastAPI(title=settings.app_name, version="1.0.0", description="Role-scoped civic grievance management APIs. Interactive documentation is available at /docs.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed"
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.status_code, "message": message, "details": exc.detail if not isinstance(exc.detail, str) else None}}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    details = [{key: value for key, value in item.items() if key not in {"input", "ctx"}} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": 422, "message": "Request validation failed", "details": details}})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": 500, "message": "An internal server error occurred"}})


@app.get("/api/health", tags=["Health"])
def health():
    return {"data": {"status": "ok"}}


app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(complaints.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(account.router, prefix="/api")
