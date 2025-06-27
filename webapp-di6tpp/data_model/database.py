import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
# Base class for declarative models
Base = declarative_base()

load_dotenv(".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

#connection string
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#endpoint to stablish connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # verifies if the connection is alive before using. stoping the 200 error 2006 ("MySQL server has gone away")
    pool_recycle=1800        # recicle coonections every 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#allows a connection for every request to the db
def get_mariadb():
    #creates a new session using SessionLocal which is created in database.py file
    db = SessionLocal()
    try:
        #while the endpoint is using the session to retrive the information from db it stays in here
        #so it can use the db
        yield db
    finally:
        #when it is done it closes the session getting db connection released
        db.close()