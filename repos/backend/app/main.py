from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app.utils.security import get_default_settlement_code, get_default_init_code

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Placeholder for routers - will be imported when routes are created
# from app.routers import teacher, auth, score, class_, student, course, term, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)

    # Initialize default config data
    db = SessionLocal()
    try:
        from app.models.models import Config

        default_configs = [
            {"key": "settlement_code", "value": get_default_settlement_code()},
            {"key": "init_code", "value": get_default_init_code()},
            {"key": "reasons", "value": '["考试","作业","荣誉","其他"]'},
        ]

        for config_data in default_configs:
            existing = db.query(Config).filter(Config.key == config_data["key"]).first()
            if not existing:
                db.add(Config(**config_data))

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Config initialization error: {e}")
    finally:
        db.close()

    yield

    # Shutdown (if needed)


app = FastAPI(title="Score Management API", lifespan=lifespan)


# Include routers when they are created
# app.include_router(teacher.router, prefix="/api/teachers", tags=["teachers"])
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(score.router, prefix="/api/scores", tags=["scores"])
# app.include_router(class_.router, prefix="/api/classes", tags=["classes"])
# app.include_router(student.router, prefix="/api/students", tags=["students"])
# app.include_router(course.router, prefix="/api/courses", tags=["courses"])
# app.include_router(term.router, prefix="/api/terms", tags=["terms"])
# app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/")
async def root():
    return {"message": "Score Management API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
