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
        from app.utils.security import hash_password
        import os

        default_configs = [
            {"key": "settlement_code", "value": get_default_settlement_code()},
            {"key": "init_code", "value": get_default_init_code()},
            {"key": "reasons", "value": '["考试","作业","荣誉","其他"]'},
        ]

        for config_data in default_configs:
            existing = db.query(Config).filter(Config.key == config_data["key"]).first()
            if not existing:
                db.add(Config(**config_data))

        # Initialize admin password if not exists
        admin_password_config = db.query(Config).filter(Config.key == "admin_password_hash").first()
        if not admin_password_config:
            default_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            hashed = hash_password(default_password)
            db.add(Config(key="admin_password_hash", value=hashed))

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
from app.routers import auth_router, course_router, class_course_router, class_router, config_router, term_router, teacher_router, settlement_router, student_router, score_router, teacher_score_router, ranking_router

app.include_router(auth_router)
app.include_router(course_router)
app.include_router(class_course_router)
app.include_router(class_router)
app.include_router(config_router)
app.include_router(term_router)
app.include_router(teacher_router)
app.include_router(settlement_router)
app.include_router(student_router)
app.include_router(score_router)
app.include_router(teacher_score_router)
app.include_router(ranking_router)


@app.get("/")
async def root():
    return {"message": "Score Management API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
