import concurrent.futures
import json
from datetime import datetime

from ..middlewares import MongoMiddleware, SpiderMiddleware
from ..settings import ChromeSettings
from .webs.profilespiderweb import ProfileSpiderWeb


class ProfileSpider(ProfileSpiderWeb):
    def __init__(self,name = "Unknown") -> None:
        super().__init__()
        self.name = name
    

    def load_metadata(self):
        with open("./metadata.json","r") as jsonfile:
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
            #citations = self.get_citation_graph_data()
            bio.update(indexes = indexes,url = url)
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
                #citations = self.get_citation_graph_data()
                bio.update(indexes = indexes,
                           url = url,
                           author_id = url.split("user=")[-1],
                           last_update = datetime.utcnow().timestamp())
                
                print(bio)
                yield bio
            
            if right_navigation == "break":
                break
            
            self.driver.get("https://scholar.google.com/"+right_navigation)

    
    def fire_threads(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
            executor.map(self.__call__,self.load_metadata())

    # #@process_spider_output
    # def __call__(self,metadata):#callback:function):
    #     chrome = ChromeSettings(set_chrome_options=False,proxy=None)
    #     self.driver = chrome.chef(url = metadata["url"])

    #     with open("D:\\Users\\mk-armah\\CODE\\PYTHON\\rate_your_lecturer\\spider\\google-scholar-spider\\data.json",'r+') as file: 
    #         file_data = json.load(file)

    #         func = lambda x: file_data[metadata["alias"]].append(x) #extracts generate item and appends to json
            
    #         with concurrent.futures.ThreadPoolExecutor() as executor:
    #             executor.map(func,self.start_requests(run_name = metadata['alias'])) 

    #         #Sets file's current position at offset.
    #         file.seek(0)
    #         # convert back to json.
    #         json.dump(file_data, file, indent = 4)
    

    @MongoMiddleware.ingest_to_mongodb
    def __call__(self,metadata,**kwargs):
        chrome = ChromeSettings(set_chrome_options=False,proxy=None)
        self.driver = chrome.chef(url = metadata["url"])     
        return self.start_requests(run_name = metadata['alias'])
    
    

if __name__ == '__main__':

    spider = ProfileSpider()
    spider.name= "UMAT"
    metadata = {"url":"https://scholar.google.com/citations?view_op=search_authors&mauthors=umat&hl=en&oi=ao",
                      "alias":"UMAT"}
    spider(metadata)
    
    spider.fire_threads()