import requests
from jsonschema import validate
from reporter.utils import number_of_days_in_month



URL = 'https://my-json-server.typicode.com/typicode/demo/posts'
SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {'type': 'number'},
        'title': {'type': 'string'}
    },
    'required': ['id']
}

## [{'id': 1, 'title': 'Post 1'}, {'id': 2, 'title': 'Post 2'}, {'id': 3, 'title': 'Post 3'}]

def test_getting_posts():
    response = requests.get(url=URL)
    recieved_posts = response.json()
    assert response.status_code == 200, 'Wrong status code'
    assert len(recieved_posts) == 3, 'Wrong number of posts'
    for item in recieved_posts:
        validate(item, SCHEMA)

    print(response.json())

def test_number_of_days_in_month():
    assert number_of_days_in_month('2022-01-05') == 31, 'Not equal 31'
    assert number_of_days_in_month('2022-02-05') == 28, 'Not equal 28'
    assert number_of_days_in_month('2020-02-05') == 29, 'Not equal 29'
    assert number_of_days_in_month('2024-02-05') == 29, 'Not equal 29'
    assert number_of_days_in_month('2022-06-05') == 30, 'Not equal 30'

