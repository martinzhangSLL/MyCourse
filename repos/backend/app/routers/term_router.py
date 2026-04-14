from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Term, TermSetting
from app.schemas.config_schema import TermCreate, TermUpdate, TermResponse
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/config/terms", tags=["terms"])


@router.get("", response_model=list[TermResponse])
def get_terms(db: Session = Depends(get_db)):
    """Get all terms with their settings."""
    terms = db.query(Term).all()
    result = []
    for term in terms:
        setting = db.query(TermSetting).filter(TermSetting.term_id == term.id).first()
        result.append(TermResponse(
            id=term.id,
            name=term.name,
            year=term.year,
            start_date=setting.start_date if setting else date.today(),
            end_date=setting.end_date if setting else date.today()
        ))
    return result


@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
def create_term(request: TermCreate, db: Session = Depends(get_db)):
    """Create a new term with its settings. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    term = Term(name=request.name, year=request.year)
    db.add(term)
    db.flush()

    term_setting = TermSetting(
        term_id=term.id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    db.add(term_setting)
    db.commit()

    return TermResponse(
        id=term.id,
        name=term.name,
        year=term.year,
        start_date=request.start_date,
        end_date=request.end_date
    )


@router.put("/{term_id}", response_model=TermResponse)
def update_term(term_id: int, request: TermUpdate, db: Session = Depends(get_db)):
    """Update term dates. Only dates can be modified. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    term = db.query(Term).filter(Term.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found"
        )

    term_setting = db.query(TermSetting).filter(TermSetting.term_id == term_id).first()
    if term_setting:
        term_setting.start_date = request.start_date
        term_setting.end_date = request.end_date
    else:
        term_setting = TermSetting(
            term_id=term_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        db.add(term_setting)

    db.commit()

    return TermResponse(
        id=term.id,
        name=term.name,
        year=term.year,
        start_date=request.start_date,
        end_date=request.end_date
    )


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term(term_id: int, db: Session = Depends(get_db)):
    """Delete a term and its settings. Requires admin authentication."""
    current_user = get_current_user(db=db)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    term = db.query(Term).filter(Term.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found"
        )

    db.query(TermSetting).filter(TermSetting.term_id == term_id).delete()
    db.delete(term)
    db.commit()
