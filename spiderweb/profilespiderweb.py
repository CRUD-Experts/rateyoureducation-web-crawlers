"""
Engineered By : Ing Michael Kofi Armah
Date created: 16/03/23
last modified: see github commit date

Description: SpiderWeb class contains the methods tailored to scrape
contents from google scholar profiles page. Each Method performs specific
task in the scraping and can be utilized independently (More like a
microservice architecture for scraping). The class supports
concurrent executions as well.

Tip: This script and the entire codebase requires the understanding some
advanced programming concepts (Not beginner friendly).If you really have to make changes,
be sure to keep track of changes you make so you can easily revert when necessary.

"""

import concurrent.futures
import json
import os
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from .middlewares import SpiderMiddleware
from .settings import ChromeSettings

spyware = SpiderMiddleware.monitor_spider_action

      
class ProfileSpiderWeb:
    name = "Profile Spider Web"
    checkpoint = ""

    @spyware
    def get_page_number(self):
        """get page number """
 
        page_number_element = WebDriverWait(
                    self.driver, 10).until(
                    EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='gs_nph gsc_pgn_ppn']")))   
         
        return page_number_element.text
    
    @spyware
    def get_scholar_elements(self):
        scholar_elements = self.driver.find_elements(by = By.XPATH,value = "//a[@class = 'gs_ai_pho']")    
        return scholar_elements  

    @spyware
    def get_scholar_urls(self):
        urls = {url_tag.get_attribute('href') for url_tag in self.get_scholar_elements()}    
        return urls
    
    @spyware
    def get_scholar_ids(self):
        obj = map(lambda x: x.split("=")[-1],self.get_scholar_urls()) 
        return set(obj)
    
    @spyware
    def navigate_page(self,right = True):
        
        """navigate Profiles by click on the arrow buttons"""

        right_button_xpath = "//button[contains(@class,'gsc_pgn_pnx')]"
        left_button_xpath = "//button[contains(@class,'gsc_pgn_ppr')]"

        try:
            page_button = WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                (By.XPATH, right_button_xpath if right else left_button_xpath))) 
            page_button.click()
        except Exception as exc:
            raise exc
        
    @spyware
    def navigate_page_v2(self,right = True):
        """navigate Profiles by click on the arrow buttons"""
        self.checkpoint = self.driver.current_url
        right_button_xpath = "//button[contains(@class,'gsc_pgn_pnx')]"
        left_button_xpath = "//button[contains(@class,'gsc_pgn_ppr')]"

        try:
            next_button = WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                (By.XPATH, right_button_xpath if right else left_button_xpath)))
            if not next_button.is_enabled():
                 return "break"
            
            url_encoded_text = next_button.get_attribute("onclick")
            url_fragment = url_encoded_text.split("=")[-1][1:-1] #get the url and remove '' from it
            http_url = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), url_fragment)
            print(http_url)
            return http_url

        except Exception as exc:
            raise exc

    @spyware
    def get_scholar_bio(self):
        """get scholar profile"""
        
        h3_tags = self.driver.find_elements(by = By.XPATH,value = "//h3[@class = 'gs_ai_name']")
        
        profile = []
        for tags in h3_tags:
            a_tags = tags.find_elements(by = By.TAG_NAME,value = 'a')
            for t in a_tags:
                url = t.get_attribute('href')
                id = url.split("=")[-1]
                profile_data = dict(name =t.text,id = id,url = url,last_update = datetime.now().timestamp())
                profile.append(profile_data)

        verified_at_elements = self.driver.find_elements(by = By.XPATH,value = "//div[@class = 'gs_ai_eml']")
        specialty_div_elements = self.driver.find_elements(by = By.CSS_SELECTOR,value = "div.gs_ai_int") #.gs_ai_int

        for enum,(v,s) in enumerate(zip(verified_at_elements,specialty_div_elements)):
            specialty_a_element = s.find_elements(by = By.CSS_SELECTOR,value = "a.gs_ai_one_int")
            print([i.text for i in specialty_a_element])
            profile[enum].update(verified_at = v.text.split(" ")[-1],specialty = [i.text for i in specialty_a_element])
            yield profile[enum]

    @spyware
    def get_scholar_bio_v2(self):
        
        name_element = WebDriverWait(
                            self.driver, 10).until(
                            EC.presence_of_element_located(
                            (By.CSS_SELECTOR, '#gsc_prf_in')))
        #name_element = self.driver.find_element(by = By.CSS_SELECTOR,value = '#gsc_prf_in')

        verified_at_element = self.driver.find_element(by = By.CSS_SELECTOR,value = "#gsc_prf_ivh")
        specialty_div_element = self.driver.find_element(by = By.CSS_SELECTOR,value = "#gsc_prf_int")
        specialty_a_element = specialty_div_element.find_elements(by = By.XPATH,value = "//a[@class = 'gsc_prf_inta gs_ibl']")
        specialty = [i.text for i in specialty_a_element]
        image_div_element = self.driver.find_element(by = By.CSS_SELECTOR,value = "#gsc_prf_pup-img")
        image = image_div_element.get_attribute("src")
        profile = dict(name = name_element.text,
                    verified_at = verified_at_element.text,
                    specialty = specialty,
                    image = image)

        return profile
    

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
            raise "Coudn't get citation data | Webdriver element was null"
        
        except exceptions.TimeoutException:
            return None

        citation_years = cited_by_div_tag.find_elements(by = By.XPATH,value = "//span[@class = 'gsc_g_t']") #years
        citation_graph = cited_by_div_tag.find_elements(by = By.XPATH,value = "//a[@class='gsc_g_a']") #number of citations of the given years
        
        num_of_citations = []
        for bar in citation_graph:
            time.sleep(2)
            bar.click()
            num_of_citations.append(bar.text)
            print(num_of_citations)
        
        zipped_data = zip([i.text for i in citation_years],num_of_citations)
        return dict(zipped_data)

    @spyware
    def get_citation_data(self):
        """get graph data from scholar page"""

        papers_tag = WebDriverWait(self.driver,5).until(EC.presence_of_all_elements_located((By.XPATH,"//a[@class='gsc_a_at']")))
        papers = [i.text for i in papers_tag]
        papers_url = [i.get_attribute('href') for i in papers_tag]

        publication_years = WebDriverWait(self.driver,5).until(EC.presence_of_all_elements_located((By.XPATH,"//span[@class='gsc_a_h gsc_a_hc gs_ibl']")))
        publication_years = [i.text for i in publication_years]
       
        citations = self.driver.find_elements(By.XPATH,"//a[@class='gsc_a_ac gs_ibl']")
        citations = [i.text for i in citations]

        result = [{"title_of_paper": p, "year_of_publication": y, "cited_by": int(c) if c != '' else 0,'link':u} for p, y, c,u in zip(papers, publication_years, citations,papers_url)]

        return result
    
    @spyware
    def get_co_authors(self):
        view_all_button_xpath = "//button[@id = 'gsc_coauth_opn']" # view all co-authors button
        list_of_co_authors_xpath = "//a[@class='gs_ai_pho']"
        page_button = self.driver.find_element(by = By.XPATH,
                                              value = view_all_button_xpath) 

        page_button.click()
        # wait for element to be present
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

    @spyware
    def get_scholar_image(self):
        """get image of scholar"""
        image_xpath = "//img[@id = 'gsc_prf_pup-img']"
        image_element = self.driver.find_element(by = By.XPATH,value = image_xpath)
        return image_element.get_attribute("src")
    

    @spyware
    def get_citation_indexes(self):
        """get scholar citation indexes from the citation table"""
        try:
            #check if citation index table is available
            citation_table_element = WebDriverWait(
                self.driver, 5).until(
                EC.presence_of_element_located(
                (By.CLASS_NAME, "gsc_rsb_sc1"))) 
            assert citation_table_element is not None
        
        except AssertionError:
            raise "Coudn't get citation indexes | Webdriver element was null"
        
        except exceptions.TimeoutException:
            return None
        
        table_labels_elements = citation_table_element.find_elements(by = By.XPATH,value = "//a[@class = 'gsc_rsb_f gs_ibl']")
        table_values_elements = citation_table_element.find_elements(by = By.XPATH,value = "//td[@class = 'gsc_rsb_std']")

        table_values = [int(i.text) if i.text != '' else 0 for enum,i in enumerate(table_values_elements) if enum%2==0 ] #get values for the 'All' column only
        table_labels = [i.text for i in table_labels_elements]
        zipped_data = zip(table_labels,table_values)
        
        return dict(zipped_data)