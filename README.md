# Bucky API

### An API to your number one to-do list application  

API Documentaion [here](https://jsapi.apiary.io/previews/buckyapi/reference) 


## Installation  

1. Install dependencies  
`pip install -r requirements.txt`  
2. Point flask to the application and database  
`export FLASK_APP=bucky_app.py`  
`export DEV_DATABASE_URL="postgresql://<username>:<password>@localhost/bucky_dev"`
 
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
