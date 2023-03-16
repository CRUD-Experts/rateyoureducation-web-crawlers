from settings import ChromeSettings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
import time
import os

import concurrent.futures
import time
import json
import sys

from selenium import webdriver
from dotenv import load_dotenv

load_dotenv(".env")
host = os.environ.get("HOST_URL")

class ScholarSpider:
    def __init__(self,driver) -> None:
        self.driver = driver

    def get_scholar_elements(self):
        scholar_elements = self.driver.find_elements(by = By.XPATH,value = "//a[@class = 'gs_ai_pho']")    
        return scholar_elements  


    def get_scholar_urls(self):
        urls = {url_tag.get_attribute('href') for url_tag in self.get_scholar_elements()}    
        return urls


    def get_scholar_bio(self):
        """get scholar profile"""
        
        h3_tags = self.driver.find_elements(by = By.XPATH,value = "//h3[@class = 'gs_ai_name']")
        
        profile = []
        for tags in h3_tags:
            a_tags = tags.find_elements(by = By.TAG_NAME,value = 'a')
            #profile = {"name":[],"id":[],"verified_at":[]}
            for t in a_tags:
                url = t.get_attribute('href')
                id = url.split("=")[-1]
                # profile['url'] = url
                # profile['name'].append(t.text)
                # profile['id'].append(id)
                profile_data = dict(name =t.text,id = id,url = url)
                profile.append(profile_data)

        verified_at_elements = self.driver.find_elements(by = By.XPATH,value = "//div[@class = 'gs_ai_eml']")
        verified_at = [{"verified_at":i.text.split(" ")[-1]} for i in verified_at_elements]
        
        zipped_data = zip(profile,verified_at)
        
        return list(zipped_data)
    
    def get_scholar_ids(self):
        obj = map(lambda x: x.split("=")[-1],self.get_scholar_urls()) 
        return set(obj)
    
    def navigate_page(self,right = True):
        """navigate Profiles by click on the arrow buttons"""

        right_button_xpath = "//button[contains(@class,'gsc_pgn_pnx')]"
        left_button_xpath = "//button[contains(@class,' gsc_pgn_ppr')]"

        try:
            page_button = WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                (By.XPATH, right_button_xpath if right else left_button_xpath))) 
            # page_button = self.driver.find_element(by = By.XPATH,
            #                                     value = right_button_xpath if right else left_button_xpath)
            page_button.click()
        except Exception as exc:
            raise exc

    
    def click_on_scholar_profile(self,atag):
        """clicks on a scholar profile to get the entire scholar page loaded"""
        atag.click()

    
    def get_co_authors(self):
        view_all_button_xpath = "//button[@id = 'gsc_coauth_opn']" #view all co-authors button
        list_of_co_authors_xpath = "//a[@class='gs_ai_pho']"
        page_button = self.driver.find_element(by = By.XPATH,
                                              value = view_all_button_xpath) 
        
        page_button.click()
        #wait for element to be present
        WebDriverWait(
                    self.driver, 10).until(
                    EC.presence_of_element_located(
                    (By.ID, "gsc_codb_content"))) 
        
        list_of_co_authors_a_tags = self.driver.find_elements(by = By.XPATH,
                                               value = list_of_co_authors_xpath)
        
        urls = {}
        func = lambda x: x.get_attribute('href')
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
              urls = executor.map(func,list_of_co_authors_a_tags)
              return urls

        # urls = {url_tag.get_attribute('href') for url_tag in list_of_co_authors_a_tags}    
        # return urls

    
    def get_citation_graph_data(self):
        """get graph data from scholar page"""
        try:
            #check if scholar has previous work over the years, i.e if graph is available
            cited_by_xpath = "//div[@class = 'gsc_md_hist_b']"
            cited_by_div_tag = WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                (By.CLASS_NAME, "gsc_md_hist_b"))) 
            assert cited_by_div_tag is not None
        
        except AssertionError as ess_error:
            raise "Coudn't get citation graph | Webdriver element was null"
        
        except exceptions.TimeoutException:
            return None

        citation_years = cited_by_div_tag.find_elements(by = By.XPATH,value = "//span[@class = 'gsc_g_t']") #years
        citation_graph = cited_by_div_tag.find_elements(by = By.XPATH,value = "//a[@class='gsc_g_a']") #number of citations of the given years

        num_of_citations = []
        for bar in citation_graph:
            bar.click()
            num_of_citations.append(bar.text)

        zipped_data = zip([i.text for i in citation_years],num_of_citations)
        return dict(zipped_data)

    
    def get_scholar_image(self):
        """get image of scholar"""
        image_xpath = "//img[@id = 'gsc_prf_pup-img']"
        image_element = self.driver.find_element(by = By.XPATH,value = image_xpath)
        return image_element.get_attribute("src")


    def get_citation_indexes(self):
        """get scholar citation indexes from the citation table"""

        try:
            #check if citation index table is available
            citation_table_xpath = "//td[@class = 'gsc_rsb_sc1']"
            citation_table_element = WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                (By.CLASS_NAME, "gsc_rsb_sc1"))) 
            assert citation_table_element is not None
        
        except AssertionError:
            raise "Coudn't get citation indexes | Webdriver element was null"
        
        except exceptions.TimeoutException:
            return None
        
        table_labels_elements = citation_table_element.find_elements(by = By.XPATH,value = "//a[@class = 'gsc_rsb_f gs_ibl']")
        table_values_elements = citation_table_element.find_elements(by = By.XPATH,value = "//td[@class = 'gsc_rsb_std']")

        table_values = [i.text for enum,i in enumerate(table_values_elements) if enum%2==0 ] #get values for the 'All' column only
        table_labels = [i.text for i in table_labels_elements]
        zipped_data = zip(table_labels,table_values)
        
        return dict(zipped_data)
   
    def __call__(self):
        urls_list = set()
        start_time = time.time()
        while True:    
            urls = self.get_scholar_urls()
            self.navigate_page()
            pre_count = len(urls_list)
            for i in urls:
                urls_list.add(i)
            if len(urls_list) == pre_count:
                break
        url_elapse_time = time.time() -start_time
        print("URL ELAPSE TIME >>> ",url_elapse_time)
        
        start_time = time.time()
        for url in urls_list:
            self.driver.get(url)
            image = self.get_scholar_image()
            #graph_data = self.get_citation_graph_data()
            indexes = self.get_citation_indexes()
            print({"image":image,"indexes":indexes})  
        profile_elapse_time = time.time() - start_time 
        print("PROFILE ELAPSE TIME >>> ",profile_elapse_time)    


    # def exit(self):
    #     self.driver.quit() 


if __name__ == '__main__':

    def driver_setup(options = False):
    
        if options == True:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
            driver = webdriver.Chrome(options=options)
        driver = webdriver.Chrome()

        return driver

    
    

    with open("./data.json","r") as jsonfile:
        jsondata = json.load(jsonfile)

    host_urls = {i['url'] for i in jsondata['data']}
    #drivers = [driver_setup() for _ in range(len(host_urls))]


    # drivers = [ChromeSettings(set_chrome_options = False).chef(url = i) for i in  host_urls]

    #host_url = "https://scholar.google.com/citations?view_op=view_org&org=14888764304008682656&hl=en&oi=io"
    # spider = LaunchSpider(driver= ChromeSettings(set_chrome_options = False).chef(url = host_url))
    # spider()


    def Spider(url):
        # driver = driver_setup()
        driver = ChromeSettings(set_chrome_options = False).chef(url = url)
        spider = ScholarSpider(driver= driver)()



    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        executor.map(Spider,host_urls)