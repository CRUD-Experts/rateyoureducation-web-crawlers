import concurrent.futures
import logging
import os

import dotenv
import pymongo
from pymongo.server_api import ServerApi

dotenv.load_dotenv()

class SpiderMiddleware:

    logging.basicConfig(filename= os.path.join(os.getcwd(),"logs.log"),
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
            
            except Exception as exc:
                __self__ = SpiderMiddleware()
                __self__.process_spider_exception(exception = exc,extra = extra,action = callback)

            finally:
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
                    
                SpiderMiddleware.logger.info(f"Monitoring {callback.__name__} Action",extra = extra)
            
            except Exception as exc:
                __self__ = SpiderMiddleware()
                __self__ .process_spider_exception(exception = exc,extra = extra,action = callback)
            
            finally:
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
        SpiderMiddleware.logger.error(exception)



class MongoMiddleware:

    client = pymongo.MongoClient(os.environ.get("MONGODB_CONNECTION_STRING"),server_api = ServerApi('1'))
    db = client.rate_your_lecturer 
    collection = db.scraped_profiles 

        
    def ingest_to_mongodb(callback):

        def func(self,metadata,**kwargs):
            """ingest scraped data inside a mongodb database"""
            try:

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    updateone = lambda doc: MongoMiddleware.collection.update_one({"author_id":doc['author_id']},{"$set":doc},upsert=True)
                    executor.map(updateone,callback(self,metadata,**kwargs))

            except Exception as exc:
                pass #report the exception to logger
            return True
        return func

        
    





# class MongoMiddleware:


#     def __init__(self) -> None:
#         client = pymongo.MongoClient(os.environ.get("MONGODB_CONNECTION_STRING"),server_api = ServerApi('1'))
#         db = client.rate_your_lecturer 
#         self.collection = db.scraped_profiles

#     class MongoStore:
#         """store scraped data inside a mongodb database"""

#         def ingest_to_mongodb(self,**kwargs):

#             document = lambda doc: self.collection.update_one({doc['author_id']},{"$set":doc},upsert=True)
            
#             with concurrent.futures.ThreadPoolExecutor() as executor:
#                 pass
#                 #print(response.matched_count)
        
    
#     class MongoLog:
#         """log spyder actions/scraping process into a mongodb database"""

#         def log_to_mongodb(self,**kwargs):
#             pass
