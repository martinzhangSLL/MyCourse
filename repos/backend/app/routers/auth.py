from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.models.models import Teacher, Config
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.utils.security import verify_password
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_admin_password(db: Session) -> str:
    """Get admin password hash from config."""
    admin_password_config = db.query(Config).filter(Config.key == "admin_password_hash").first()
    if admin_password_config:
        return admin_password_config.value
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Admin password not initialized"
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if request.role == "admin":
        if request.username != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        admin_password_hash = get_admin_password(db)
        if not verify_password(request.password, admin_password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = create_access_token({"user_id": 0, "role": "admin"})
        return LoginResponse(
            token=token,
            user=UserResponse(id=0, name="admin", role="admin")
        )

    elif request.role == "teacher":
        teacher = db.query(Teacher).filter(Teacher.name == request.username).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not verify_password(request.password, teacher.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = create_access_token({"user_id": teacher.id, "role": "teacher"})
        return LoginResponse(
            token=token,
            user=UserResponse(id=teacher.id, name=teacher.name, role="teacher")
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)
