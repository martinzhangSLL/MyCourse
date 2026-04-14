from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine, SessionLocal


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
            {"key": "settlement_code", "value": "123456"},
            {"key": "init_code", "value": "888888"},
            {"key": "reasons", "value": "课堂表现,作业完成,考试进步,帮助他人,值日工作"},
        ]

        for config_data in default_configs:
            existing = db.query(Config).filter(Config.key == config_data["key"]).first()
            if not existing:
                db.add(Config(**config_data))

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing config: {e}")
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
