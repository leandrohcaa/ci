from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.routes import courses, enrollments, users, users_async

app = FastAPI(title="BEON High School API")
register_exception_handlers(app)

app.include_router(users.router)
app.include_router(users_async.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
