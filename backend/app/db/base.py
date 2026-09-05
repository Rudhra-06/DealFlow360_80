from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.x ORM models in DealFlow360.
    
    Every future database model will inherit from this Base class to register
    with SQLAlchemy's Model Declarative Meta mapping.
    """
    pass
