from sqlalchemy import Column, String, Float, Integer, DateTime, func
from .database import Base  


class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer)
    title = Column(String)
    rating = Column(Float)
    review = Column(String)
    review_date = Column(DateTime(timezone=True), server_default=func.now())
