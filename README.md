[![Build Status](https://travis-ci.org/arnawldo/bucky_api.svg?branch=master)](https://travis-ci.org/arnawldo/bucky_api)
[![Coverage Status](https://coveralls.io/repos/github/arnawldo/bucky_api/badge.svg)](https://coveralls.io/github/arnawldo/bucky_api)  
# Bucky API

### An API to your number one to-do list application  

API Documentaion [here](https://jsapi.apiary.io/previews/buckyapi/reference) 


## Installation  

1. Install dependencies  
`pip install -r requirements.txt`  
2. Point flask to the application 
`export FLASK_APP=bucky_app.py`  

3. Set path to database  
- For development
`export DEV_DATABASE_URL="postgresql://<username>:<password>@localhost/bucky_dev"`  
- For production  
`export DATABASE_URL="postgresql://<username>:<password>@localhost/bucky_dev"`  
  Remember to set app config to production in `bucky_app.py`


3. Initialize database  
`flask db init`  
`flask db migrate`  
`flask db upgrade`  

3. Fire it up  
`flask run`  


## Testing

One may run tests with:  
1. `pip install -r test_requirements.txt` (one time)  
2. `export TEST_DATABASE_URL="postgresql://<username>:<password>@localhost/bucky_test"`  
3. `python setup.py test`
