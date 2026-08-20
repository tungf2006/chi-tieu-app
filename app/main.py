from fastapi import FastAPI

from app import __version__
from app.api.routes import transactions, categories, reports, forecast
from app.core.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title="Chi Tieu API", version=__version__)

    # Tạo bảng trong DB nếu chưa có
    Base.metadata.create_all(bind=engine)

    # Include routers
    app.include_router(transactions.router)
    app.include_router(categories.router)
    app.include_router(reports.router)
    app.include_router(forecast.router)

    @app.get("/")
    def read_root():
        return {"message": "Hello World"}

    return app


app = create_app()