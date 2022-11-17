from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas


def create_review(db: Session, review_obj: schemas.Review):
    db_review = models.Review(
        book_id=review_obj.book_id,
        title=review_obj.title,
        rating=review_obj.rating, 
        review=review_obj.review,
        review_date=review_obj.review_date
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

def query_ratings(db: Session, book_id: int) -> list:
    query_result = db.query(
        func.avg(models.Review.rating).label('avg')
    ).filter(models.Review.book_id==book_id)

    return query_result[0][0]

def query_reviews(db: Session, book_id: int) -> list:
    query_result = db.query(models.Review).filter_by(book_id=book_id)
    return [review.review for review in query_result]

def query_n_best_books(db: Session, n_books: int) -> dict:
    query_result = db.query(
        models.Review.book_id, 
        models.Review.title, 
        func.avg(models.Review.rating).label('avg_rtg'),
        func.count(models.Review.rating).label('rtg_count')
    ).group_by(models.Review.book_id).order_by('avg_rtg')[-n_books:]

    return query_result

def query_rating_per_month(book_id: int, db: Session) -> list:
    query_result = db.query(
        models.Review.title,
        func.extract('year', models.Review.review_date),
        func.extract('month', models.Review.review_date),
        func.avg(models.Review.rating).label('avg_rtg'),
        func.count(models.Review.rating).label('count'),
    ).filter(
        models.Review.book_id==book_id
    ).group_by(
        func.extract('year', models.Review.review_date),
        func.extract('month', models.Review.review_date)
    )
    return query_result
        