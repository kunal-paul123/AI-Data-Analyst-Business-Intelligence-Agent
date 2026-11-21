import os
from fastapi import FastAPI, Request
from backend.routers import analytics, chat
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

os.makedirs("charts", exist_ok=True)

app.mount("/charts", StaticFiles(directory="charts"), name="charts")

app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI data analyst is running"}

# Handle HTTP errors (404, 401, 403, etc.)
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException
):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "message": str(exception.detail),
        },
    )


# Handle request validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Invalid request. Please check your input.",
            "errors": exception.errors(),
        },
    )



