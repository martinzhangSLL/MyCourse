import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Config
from app.schemas.config_schema import ReasonsResponse, CodesResponse, CodesUpdate
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/reasons", response_model=ReasonsResponse)
def get_reasons(db: Session = Depends(get_db)):
    """Get the list of score reasons (add/deduct reasons)."""
    config = db.query(Config).filter(Config.key == "reasons").first()
    if not config:
        return ReasonsResponse(reasons=[])
    try:
        reasons = json.loads(config.value)
        if not isinstance(reasons, list):
            reasons = []
    except (json.JSONDecodeError, TypeError):
        reasons = []
    return ReasonsResponse(reasons=reasons)


@router.put("/reasons", response_model=ReasonsResponse)
def update_reasons(request: ReasonsResponse, db: Session = Depends(get_db)):
    """Update the list of score reasons. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    config = db.query(Config).filter(Config.key == "reasons").first()
    if config:
        config.value = json.dumps(request.reasons, ensure_ascii=False)
    else:
        config = Config(key="reasons", value=json.dumps(request.reasons, ensure_ascii=False))
        db.add(config)

    db.commit()
    return ReasonsResponse(reasons=request.reasons)


@router.get("/codes", response_model=CodesResponse)
def get_codes(db: Session = Depends(get_db)):
    """Get settlement and init codes. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    settlement_config = db.query(Config).filter(Config.key == "settlement_code").first()
    init_config = db.query(Config).filter(Config.key == "init_code").first()

    return CodesResponse(
        settlement_code=settlement_config.value if settlement_config else "",
        init_code=init_config.value if init_config else ""
    )


@router.put("/codes", response_model=CodesResponse)
def update_codes(request: CodesUpdate, db: Session = Depends(get_db)):
    """Update settlement and init codes. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    settlement_config = db.query(Config).filter(Config.key == "settlement_code").first()
    if settlement_config:
        settlement_config.value = request.settlement_code
    else:
        settlement_config = Config(key="settlement_code", value=request.settlement_code)
        db.add(settlement_config)

    init_config = db.query(Config).filter(Config.key == "init_code").first()
    if init_config:
        init_config.value = request.init_code
    else:
        init_config = Config(key="init_code", value=request.init_code)
        db.add(init_config)

    db.commit()
    return CodesResponse(
        settlement_code=request.settlement_code,
        init_code=request.init_code
    )
