"""
Engineered By : Ing Michael Kofi Armah
Date created: 16/03/23
last modified: see github commit date

Purpose : Ingest Data to MongoDB 
"""

import concurrent.futures
import logging
import pymongo
import dotenv
import os

dotenv.load_dotenv()

from pymongo.server_api import ServerApi

class MongoStore:
    """store scraped data inside a mongodb database"""
    def __init__(self) -> None:
        client = pymongo.MongoClient(os.environ.get("MONGODB_CONNECTION_STRING"),server_api = ServerApi('1'))
        db = client.rate_your_lecturer 
        self.collection = db.scraped_profiles


    def Ingest_to_Mongo(self):
        response = self.collection.update_many({},{"$set":{"email":"example@gmail.com"}},upsert=True)
        print(response.matched_count)
    def Log_to_Mongo(self):
        pass

if __name__ == "__main__":
    connection = MongoStore()
    connection.Ingest_to_Mongo()