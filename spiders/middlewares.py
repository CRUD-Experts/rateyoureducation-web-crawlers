import logging

class SpiderMiddleware:

    logging.basicConfig(filename= "logs.log",
                    level = logging.INFO,
                    format = '%(asctime)s | %(levelname)s | %(run_name)-4s | %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
    
    
    def spider_opened(callback:callable):
        def func(self,**kwargs):
            extra = {'run_name': kwargs['run_name'] if kwargs['run_name'] else self.name}
            SpiderMiddleware.logger = logging.getLogger('googlescholarspider')
            SpiderMiddleware.logger.info("Spider opened: %s" % "Starting Requests ...",extra = extra)
            return callback(self,**kwargs)
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
                SpiderMiddleware().process_spider_exception(exception = exc,action = callback)

            return response
        return func
    

    def store_metrics():
        pass
    
    def process_spider_output(self,callback):
        def func(**kwargs):
            pass

    def process_spider_exception(self,exception, action):
        # Called when a spider or monitor_spider_action() method
        # (from other spider middleware) raises an exception.

        # Should return either None  or an iterable of Request or item objects.
        print("Exception Occured !!!")
        logging.error(exception)
        pass


