import requests
from jsonschema import validate
# from reporter.utils import number_of_days_in_month
# E   ModuleNotFoundError: No module named


URL = 'https://my-json-server.typicode.com/typicode/demo/posts'
SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {'type': 'number'},
        'title': {'type': 'string'}
    },
    'required': ['id']
}

def test_getting_posts():
    response = requests.get(url=URL)
    recieved_posts = response.json()
    assert response.status_code == 200, 'Wrong status code'
    assert len(recieved_posts) == 3, 'Wrong number of posts'
    validate(recieved_posts, SCHEMA)

    print(response.json())

## [{'id': 1, 'title': 'Post 1'}, {'id': 2, 'title': 'Post 2'}, {'id': 3, 'title': 'Post 3'}]