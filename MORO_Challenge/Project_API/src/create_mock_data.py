import datetime as dt
import random 
from utils import models, schemas
from utils.call_gutendex import call_gutendex
from utils.database import SessionLocal


def create_mock_review(review_obj: schemas.Review) -> schemas.Review:

    db = SessionLocal()

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

    db.close()

    return review_obj


def delete_by_id(delete_obj: schemas.Review) -> None:
    db = SessionLocal()

    del_query = db.query(
        models.Review
    ).filter(
        book_id==delete_obj.book_id,
        title==delete_obj.title,
        rating=delete_obj.rating, 
        review=delete_obj.review,
        review_date=delete_obj.review_date
    ).first()
        
    if del_query is not None:
        db.delete(del_query)
        db.commit()

    db.close()



reviews_sample = [
    'Very good book!',
    'Nice book.',
    'I did not like it',
    'It was a please-read book',
    'Interesting one!',
    'Bad book.',
    'I spent two weeks reading the book, and it surprised me every time',
    'Excellent!',
    'Boring book',
]

ratings_sample = [
    4.8,
    4,
    2.3,
    4.3,
    3.7,
    1.8,
    4.2,
    4.5,
    2.9,
]

base = dt.datetime.now()
dates_list = [base - dt.timedelta(days=x) for x in range(1000)] 
book_ids_sample = [random.randint(1, 100) for _ in range(100)]

for book_id in book_ids_sample:
    try:
        random_choice = random.randint(0, len(reviews_sample)-1)
        gutendex_response = call_gutendex('ids', book_id)
        book_title = gutendex_response['results'][0]['title']

        review_obj = schemas.Review(
                book_id=book_id, 
                title=book_title,
                rating=ratings_sample[random_choice],
                review=reviews_sample[random_choice],
                review_date=random.choice(dates_list)
        )

        create_mock_review(review_obj)
        print('Review created successfully.')        

    except IndexError:
        continue
