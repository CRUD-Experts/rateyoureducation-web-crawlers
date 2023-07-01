import concurrent.futures
import logging
import os

import dotenv
import pymongo
from pymongo.server_api import ServerApi
from selenium.common import exceptions
import json
from datetime import datetime, timedelta


dotenv.load_dotenv()

class SpiderMiddleware:

    logging.basicConfig( filename = "./store/logs.log",
                    level = logging.INFO,
                    format = '%(asctime)s | %(levelname)s | %(run_name)-4s | %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


    def spider_opened(callback:callable):
        def func(self,**kwargs):

            try:
                extra = {'run_name': kwargs['run_name'] if kwargs['run_name'] else self.name}
                SpiderMiddleware.logger = logging.getLogger('googlescholarspider')
                SpiderMiddleware.logger.info("Spider opened: %s" % "Starting Requests ...",extra = extra)
                response = callback(self,**kwargs)
                print("""
        -------------------------------worker----------------------------------
        ***********   **********   *   * * *      *********   * * *  *      
        *             *        *   *   *     *    *           *        *
        *             *        *   *   *      *   *           *        * 
        ***********   **********   *   *      *   *********   * * * *  
                  *   *            *   *      *   *           *       *     
                  *   *            *   *     *    *           *        *        
        ***********   *            *   * * *      *********   *        *                 
        ------------------------------------------------------------------
        ------------- xxxxx by: Ing Michael Kofi Armah xxxxx -------------
                    """)
            
            except Exception as exc:
                __self__ = SpiderMiddleware()
                __self__.process_spider_exception(exception = exc,extra = extra,action = callback)
                raise exc
            else:
                return response
        return func


    def monitor_spider_action(callback:callable):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        def func(self,**kwargs):
            extra = {'run_name': self.name} # if kwargs['run_name'] else self.name
            
            try:
                response = callback(self,**kwargs)
                if callback.__name__.__contains__("page_number"):
                    SpiderMiddleware.logger.info(f"Navigating through Page {response}",extra = extra)
                
                #create checkpoint for each url scraped; to be used for retry in case of run failure
                if callback.__name__.__contains__("navigate_page"): 
                    SpiderMiddleware.logger.info(f"---- Checkpoint -----",extra = extra)            
                    
                SpiderMiddleware.logger.info(f"Monitoring {callback.__name__} action",extra = extra)

            except Exception as exc:
                __self__ = SpiderMiddleware()

                __self__.process_spider_exception(exception = exc,extra = extra,action = callback)
                raise exc
              
            else:
                return response
        
        return func
    

    def store_metrics():
        """process and store spider log metrics"""
        pass


    def process_spider_output(self,callback):
        def func(**kwargs):
            pass

    def process_spider_exception(self,exception, action,extra,**kwargs):
        # Called when a spider or monitor_spider_action() method
        # (from other spider middleware) raises an exception.

        # Should return either None  or an iterable of Request or item objects.
        print("Exception Occured !!!")
        SpiderMiddleware.logger.error(exception,extra = extra)


class MongoMiddleware:
    MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")

    client = pymongo.MongoClient(MONGODB_CONNECTION_STRING,server_api = ServerApi('1'))
    db = client.rate_your_lecturer 
    staging_collection = db.staging 
    control_collection = db.control
    metadata_collection = db.metadata

    def load_metadata(data:dict):
        try:
            group = MongoMiddleware.metadata_collection.find(data)
        except Exception as e:
            raise Exception("could not get group from db: ",e)
        return group
    
    def ingest_to_mongodb(callback):

        def func(self,metadata,**kwargs):
            """ingest scraped data inside a mongodb database"""
            try:

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    updateone = lambda doc: MongoMiddleware.staging_collection.update_one({"author_id":doc['author_id']},{"$set":doc},upsert=True)
                    executor.map(updateone,callback(self,metadata,**kwargs))

            except Exception as exc:
                #raise Exception(f"Unable to insert data into Staging Database:\n{exc.__cause__}") from exc
                pass
            return True
        return func
    
    def create_retry_checkpoint(self,alias,checkpoint,**kwargs):
        MongoMiddleware.metadata.update_one({"alias":alias},{"$set":{"checkpoint":checkpoint}})
        print("checkpoint created")
    
    def controller(metadata):
        
        try:

            MongoMiddleware.control_collection.create_index("date_created", expireAfterSeconds=3600)
            MongoMiddleware.control_collection.insert_one({"org":metadata['org'],
                                                           "verified_at":metadata['verified_at'],
                                                           "date_created":datetime.now(),
                                                           "expiry_time": datetime.utcnow() + timedelta(minutes=30)})
        except Exception as exc:
            raise Exception(f"Unable to insert data into Control Database:\n{exc.__cause__}") from exc
        return True
            

class JsonMiddleware:

    def ingest_to_json(callback):

        def func(self,metadata,**kwargs):
            try:
                with open("store/data.json",'r+') as file:
                    file_data = json.load(file)

                    func = lambda x: file_data[metadata["alias"]].append(x) # extracts generate item and appends to json
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        executor.map(func,callback(self,metadata,**kwargs)) 

                    # Sets file's current position at offset.
                    file.seek(0)
                    # convert back to json.
                    json.dump(file_data, file, indent = 4)
            except Exception as exc:
                raise exc
            return
        return func
