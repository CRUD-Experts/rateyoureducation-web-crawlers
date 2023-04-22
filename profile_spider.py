import concurrent.futures
import json
from datetime import datetime
import os
import sys
 
# --- airflow import setup -----
# from google_scholar_spider.spiderweb.profilespiderweb import ProfileSpiderWeb
# from google_scholar_spider.spiderweb.settings import ChromeSettings
# from google_scholar_spider.spiderweb.middlewares import SpiderMiddleware,JsonMiddleware, MongoMiddleware

from spiderweb.profilespiderweb import ProfileSpiderWeb
from spiderweb.settings import ChromeSettings
from spiderweb.middlewares import SpiderMiddleware,JsonMiddleware, MongoMiddleware


class ProfileSpider(ProfileSpiderWeb):
    def __init__(self,name = "Unknown") -> None:
        super().__init__()
        self.name = name
    

    def load_metadata(self): 
        with open("store/metadata.json","r") as jsonfile:
            jsondata = json.load(jsonfile)
        metadata = [{"url":i['url'],"alias":i['alias']} for i in jsondata['data']]
        return metadata


    def start_concurrent_requests(self):
        """get scholar profiles for each url concurrently"""
        def func(url):
            driver = ChromeSettings(set_chrome_options=False,proxy=None).chef(url = url)
            driver.get(url) 
            self.driver = driver
            bio = self.get_scholar_bio_v2()
            indexes = self.get_citation_indexes()
            citations = self.get_citation_data()
            bio.update(indexes = indexes,url = url,citations=citations)
            print(bio)

        while True:
            page_number_store = ""
            page_number = self.get_page_number()
            print("page_number")             
            if page_number == page_number_store:
                break
            
            urls = self.get_scholar_urls()
            right_navigation = self.navigate_page_v2() #get the right navigation url

            with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
                executor.map(func,urls)

        page_number_store = page_number
        self.driver.get("https://scholar.google.com/"+right_navigation)


    @SpiderMiddleware.spider_opened
    def start_requests(self,**kwargs):
        """get user profiles and links from first page"""
        print("STarTing Requests")
        self.name = kwargs['run_name']
        while True: 

            page_number = self.get_page_number()           
            urls = self.get_scholar_urls()
            right_navigation = self.navigate_page_v2() #get the right navigation url
             
            for url in urls:
                self.driver.get(url) 
                bio = self.get_scholar_bio_v2()
                indexes = self.get_citation_indexes()
                citations = self.get_citation_data()
                bio.update(indexes = indexes,
                           url = url,
                           citations = citations,
                           author_id = url.split("user=")[-1],
                           last_update = datetime.utcnow().timestamp())
                
                print(bio)
                yield bio
            
            if right_navigation == "break":
                self.checkpoint = ''
                self.driver.quit()
                break
            
            self.driver.get("https://scholar.google.com/"+right_navigation)

    
    def fire_threads(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
            executor.map(self.__call__,self.load_metadata())
    

    @MongoMiddleware.ingest_to_mongodb
    def __call__(self,metadata,**kwargs):
        """starts requests and ingests data to mongodb
           no retries or recovery after failure, use 
           ProfileSpider.crawl instead for more retries
        """
        
        chrome = ChromeSettings(set_chrome_options=False,proxy=None)
        self.driver = chrome.chef(url = metadata["url"])     
        return self.start_requests(run_name = metadata['alias'])
        
    def crawl(self,metadata):
        """uses retries to persist failures"""
        PAGE_RETRIES = 0
        AFTER_AUTHOR = ''
        while True:
            self.__call__(metadata)      
            #spider.fire_threads()
            print("checkpoint :", self.checkpoint)
            if self.checkpoint:
                page_number = self.checkpoint.split('start=')[-1]
                after_author = self.checkpoint.split('after_author=')[-1].split('&')[0]
                print("after author:",AFTER_AUTHOR)
                print("page retries:",PAGE_RETRIES)
                if after_author == AFTER_AUTHOR and PAGE_RETRIES > 5:
                    break
                elif after_author == AFTER_AUTHOR:              
                    PAGE_RETRIES+=1 
                else:
                    AFTER_AUTHOR = after_author
                    PAGE_RETRIES+=1

                metadata['url'] = self.checkpoint
                self.driver.quit()           
                continue
            else:
                break
    
    

if __name__ == '__main__':
    
    metadata = {"url":"https://scholar.google.com/citations?view_op=view_org&hl=en&org=5976495280852929187",
                "alias":"UG"}
    
    spider = ProfileSpider()
    spider.crawl(metadata=metadata)

    # PAGE_RETRIES = 0
    # AFTER_AUTHOR = ''
    # while True:
    #     spider = ProfileSpider()
    #     spider(metadata)      
    #     #spider.fire_threads()
    #     print("checkpoint :", spider.checkpoint)
    #     if spider.checkpoint:
    #         page_number = spider.checkpoint.split('start=')[-1]
    #         after_author = spider.checkpoint.split('after_author=')[-1].split('&')[0]
    #         print("after author:",AFTER_AUTHOR)
    #         print("page retries:",PAGE_RETRIES)
    #         if after_author == AFTER_AUTHOR and PAGE_RETRIES > 5:
    #             break
    #         elif after_author == AFTER_AUTHOR:              
    #             PAGE_RETRIES+=1 
    #         else:
    #             AFTER_AUTHOR = after_author
    #             PAGE_RETRIES+=1

    #         metadata['url'] = spider.checkpoint
    #         spider.driver.quit()           
    #         continue
    #     else:
    #         break