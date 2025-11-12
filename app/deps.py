from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db


def get_settings_dep() -> Settings:
    return get_settings()


def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db
