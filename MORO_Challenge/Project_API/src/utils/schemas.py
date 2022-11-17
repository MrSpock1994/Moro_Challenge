from pydantic import BaseModel 
import datetime as dt


class Review(BaseModel):
    '''
    Class Review: This class contains the attributes for 
    the creation of reviews in the database.
    '''
    book_id: int 
    title: str
    rating: float 
    review: str
    review_date: dt.datetime

class DisplayReview(Review):
    class Config:
        orm_mode = True 

class ReviewBase(BaseModel):
    '''
    ReviewBase Class: This class contains the attributes
    which will be used in the Review Class. This class was
    created to help with the API calling when writing reviews.
    '''
    book_id: int 
    rating: float 
    review: str
