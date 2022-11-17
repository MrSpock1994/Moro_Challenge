import json 
import requests

def call_gutendex(query_type, query):
    # Calling the 3rd party API to get the book results
    response_raw = requests.get(f'https://gutendex.com/books/?{query_type}={query}')

    # Decoding and loading the response to the request
    dict_str = response_raw.content.decode("UTF-8")
    return json.loads(dict_str)

    