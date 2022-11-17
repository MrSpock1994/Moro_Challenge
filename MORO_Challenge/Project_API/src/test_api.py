import pytest
import http.client
from fastapi.testclient import TestClient   
from utils import models, schemas
from utils.database import SessionLocal

from .main import app



client = TestClient(app)


def test_get_book():
    response = client.get("/get_book?request=Frankenstein")
    assert http.client.OK == response.status_code


def test_get_book_should_throw_error():
    response = client.get("/get_book?request=THIS_SHOULD_NOT_BE_FOUND")
    assert http.client.NOT_FOUND == response.status_code

def test_post_review():
    url = "/post_review"
    payload = {
    "book_id": 84,
    "rating": 5,
    "review": "This is a test review"
    }
    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }
    response = client.post(url, headers=headers, json=payload)
    assert http.client.CREATED == response.status_code

def test_get_review():
    response = client.get("/get_reviews?book_id=84")
    assert http.client.OK == response.status_code


def test_get_review_should_throw_error():
    response = client.get("/get_reviews?book_id=-3")
    assert http.client.NOT_FOUND == response.status_code

def test_post_review():
    url = "/post_review"
    payload = {
    "book_id": 84,
    "rating": 5,
    "review": "This is a test review"
    }
    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }
    response = client.post(url, headers=headers, json=payload)
    assert http.client.CREATED == response.status_code

def test_get_n_best_books():
    response = client.get('/get_n_best_books?n_books=10')
    assert http.client.OK == response.status_code

def test_get_n_best_books_should_throw_error():
    response = client.get('/get_n_best_books?n_books=-5')
    assert http.client.UNPROCESSABLE_ENTITY == response.status_code


def test_get_book_rating_per_month():
    response = client.get('/get_book_rating_per_month?book_id=84')
    assert http.client.OK == response.status_code
    

def test_get_book_rating_per_month_should_throw_error():
    response = client.get('/get_book_rating_per_month?book_id=-5')
    assert http.client.UNPROCESSABLE_ENTITY == response.status_code

# Now we simply delete the book we inserted in the database
# while testing
def test_should_delete_test_review():
    db = SessionLocal()

    del_query = db.query(
        models.Review
    ).order_by(
        models.Review.id.desc()
    ).first()
        
    print(del_query)  
    if del_query is not None:
        db.delete(del_query)
        db.commit()

    db.close()

    assert True