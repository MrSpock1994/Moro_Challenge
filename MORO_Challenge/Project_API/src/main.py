import datetime as dt
from fastapi import Depends, FastAPI, HTTPException
from http import HTTPStatus
from sqlalchemy.orm import Session
from utils import models, schemas, crud
from utils.database import SessionLocal, engine
from utils.call_gutendex import call_gutendex # function to call the 3rd party API

# Creates the database
models.Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

cache = {} # Cache for search of book titles
cache_id = {} # Cache for search of book ids

HANDLE_PAGINATION = False

########################################################################
# Construct the required dictionary to be displayed in the API's response
########################################################################
def construct_response_dict(result):
    return_value = {
            'id': result['id'],
            'title': result['title'],
            'authors': result['authors'],
            'languages': result['languages'],
            'download_count': result['download_count'],
        }
    return return_value

########################################################################
# Handling pagination
########################################################################
def handle_pagination(response: dict, request: str, previous_result: dict = None, page: int = 0) -> dict:
    '''
    This function handles with the pagination format of the Gutendex API.
    It is a recursive function that calls itself to construct a structure
    similar to the one in the Gutendex; there is the keys previous, results
    and next. previous and next refers to the previous and next pages in the
    Gutendex index, with the information explicitly passed (in Gutendex, the
    previous and next information is stored in a url)
    '''
    status_dict = {'previous': previous_result or None}

    # Iterating over all results and retrieving the necessary information
    results = [construct_response_dict(result) for result in response['results']] 
    status_dict['results'] = {'books': results}

    # Maximum number of pages to be displayed. Here it is fixed in 5
    # to avoid any memory issue and to not let the query take a long time
    MAX_NUM_OF_PAGES = 5
    if not response['next'] or page == MAX_NUM_OF_PAGES:
        status_dict['next'] = None

    else:
        next_page = response['next']
        next_page = next_page.split('books/?')[1]
        next_page = next_page.split('search=')[0]
        next_page = f'{next_page}search'
        next_response = call_gutendex(next_page, request)
        status_dict['next'] = handle_pagination(
            next_response, 
            request, 
            previous_result=status_dict.copy(),
            page=page+1
        )
    
    return status_dict

########################################################################
# Endpoint to search for books
########################################################################
@app.get("/get_book")
def get_book(request: str = None) -> dict:
    '''
    Searchs for a book title in the Gutendex API.

    Inputs:
    - request: string with the book title to be searched on Gutendex 

    Outputs:
    - return_value: dict with the information about the book 
    from the Gutendex query
    '''
   
    if request in cache:
        return cache[request]

    # Here, I'm limiting the size of the cache; 
    # I'm choosing 300 as an example to avoid any memory issue in this simple example,
    # but the choice must be made according to the server in which the API will be hosted.     
    # NOTE: In recent versions of python, the dictionary is ordered. Thus, excluding the 
    # first key in the dictionary represents the FIFO caching mechanism. This strategy
    # can be changed according to the company needs
    if len(cache) == 300:
        key_popped = cache.pop(list(cache.keys())[0], None)

    # Querying Gutendex to find matching books
    if not request:
        return {'books': []}
    
    response = call_gutendex('search', request)
    if len(response['results']) == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Book not found in Gutendex database")

    if HANDLE_PAGINATION:
        return_value = handle_pagination(response, request)    
    else:
        # Iterating over all results
        results = [construct_response_dict(result) for result in response['results']] 
        # The return value as specified in the problem description
        return_value = {'books': results}
        
    # Saving the result in the cache
    cache[request] = return_value

    return return_value
    
########################################################################
# Endpoint for writing ratings and reviews for the books
########################################################################
@app.post('/post_review', status_code=HTTPStatus.CREATED) 
def post_review(request: schemas.ReviewBase, db: Session = Depends(get_db)) -> dict:
    '''
    Saves the review on the database

    Inputs:
    - request: Information about the the book review

    Outputs:
    - dictionary with the review information
    '''
    
    # Calling Gutendex
    gutendex_response = call_gutendex('ids', request.book_id)
    if len(gutendex_response['results']) > 0: # Checks if the book was found
        book_title = gutendex_response['results'][0]['title']
        
        review_obj = schemas.Review(
            book_id=request.book_id, 
            title=book_title,
            rating=request.rating,
            review=request.review,
            review_date=dt.datetime.now()
        )

        # Handling unprocessable entities in the POST
        if not 0 <= review_obj.rating <= 5:
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="The book rating must be between 0 and 5")
        if not review_obj.review:
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="The review field cannot be empty")

        # Saving to the database
        crud.create_review(db=db, review_obj=review_obj)

        # Returning the review object to the user
        return {'Review': review_obj}
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Book not found in Gutendex database")
    
########################################################################
# Endpoint to search for books with their information and reviews
########################################################################
@app.get('/get_reviews')
def get_reviews(book_id: int, db: Session = Depends(get_db)) -> dict:
    '''
    Gets all the reviews of a given book (selected by ID)

    Inputs:
    - book_id: Book ID

    Outputs:
    - return_value: Dictionary with the information about the book,
    its average rating and all the reviews
    '''
    # Check if there is a match for the id
    if book_id in cache_id:
        response = cache_id[book_id]
    else:
        # Getting the query from Gutendex
        response = call_gutendex('ids', book_id)
        # Make sure there is the book with the given ID
        if len(response['results']) == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Book ID not found")
        cache_id[book_id] = response

    if len(cache_id) > 300:
        key_popped = cache.pop(list(cache_id.keys())[0], None)
    
    # Structuring the response object with the 
    # information from the Gutendex query
    for result in response['results']:
        dict_to_return = {
            'id': result['id'],
            'title': result['title'],
            'authors': result['authors'],
            'languages': result['languages'],
            'download_count': result['download_count'],
        }

    try:
        avg_rating = crud.query_ratings(db=db, book_id=book_id)
        # Creating the rating key for the returning object
        dict_to_return['rating'] = round(avg_rating, 2)
        # Getting a list with all the reviews for the specific book
        reviews = crud.query_reviews(db=db, book_id=book_id)
        # Creating a reviews key for the returning object
        dict_to_return['reviews'] = reviews
    except TypeError: # If there's no entity in the query return, round(avg_rating, 2) will throw a TypeError exception
        dict_to_return['rating'] = None 
        dict_to_return['review'] = []
        
    return dict_to_return
    
########################################################################
# Endpoint for the search of the N best books in the database
########################################################################
@app.get('/get_n_best_books')
def get_n_best_books(n_books: int, db: Session = Depends(get_db)) -> dict:
    '''
    Inputs:
    - n_books: The number of best books to be returned by the query 

    Outputs:
    - return_value: A dictionary with a list with all the n_books according
    to their average rating, containing their information about the book id,
    book title, average rating and number of reviews registered.
    '''
    if n_books <= 0:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="The numbers of books to be displayed must be greater than zero.")

    response = crud.query_n_best_books(db=db, n_books=n_books)

    if len(response) == 0: # Empty database
        return {'books': []}

    return_value = {'books': []}
    for book in response[::-1]:
        return_value['books'].append({
            'BookId': book[0],
            'Title': book[1],
            'AverageRating': round(book[2],2),
            'NumberOfReviews': book[3],
        })

    return return_value

########################################################################
# Endpoint for the search of the average rating of a book per month
########################################################################
@app.get('/get_book_rating_per_month')
def get_book_rating_per_month(book_id: int, db: Session = Depends(get_db)) -> dict:
    '''
    Generates the average rating of a book per month

    Inputs:
    - book_id: The id of the book

    Outputs:
    - return_value: The dictionary with the information about the
    average rating of the book per month
    '''
   
    response = crud.query_rating_per_month(db=db, book_id=book_id)

    # FastAPI already deals with wrong type parameters
    # if type(book_id) != int:
    #     raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="Please, enter a positive integer")

    if book_id <= 0:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="The book IDs must be greater than zero")

    return_value = {'books': []}

    if response.count() == 0:
        return return_value

    for month in response:
        return_value['books'].append({
            'BookId': book_id,
            'Title': month[0],
            'Year': month[1],
            'Month': month[2],
            'AverageRating': round(month[3],2),
            'MonthCount': month[4],
        })
    
    return return_value


