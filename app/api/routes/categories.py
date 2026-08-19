from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()