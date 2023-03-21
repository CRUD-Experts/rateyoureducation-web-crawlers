import datetime
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# # proxies = [
#    174.138.184.82:42409,
#66.70.235.23:8080
# ]


class ChromeSettings:
    def __init__(self,proxy = None,set_chrome_options = True):
        self.set_chrome_options = set_chrome_options
        self.proxy = "http://7f53c02466844038c2740959d82cf520f25e1ed5:js_render=true&antibot=true&premium_proxy=true@proxy.zenrows.com:8001" 
    def _set_chrome_options(self) -> None:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        #chrome_options.add_argument('--proxy-server=%s' % self.proxy)
        chrome_prefs = {}
        chrome_options.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        return chrome_options

    def chef(self,url: str):
        """
        Establishes connection with hyperlinks and return soup object
        Args:
            
            url:str | url to scrape
            driver:webdriver object | an already existing driver which has knowledge of a pre-assigned url
        Returns:      
            soup:beautiful soup object
            driver:webdriver object           
            """
        driver = webdriver.Chrome(chrome_options  = self._set_chrome_options(),options = ChromeDriverManager().install())    \
                    if self.set_chrome_options is True else  webdriver.Chrome()       #

        driver.get(url)
        try:
            WebDriverWait(
                driver, 50).until(
                EC.presence_of_element_located(
                    (By.ID, "gs_bdy_ccl")))
        except TimeoutException as timeout:
            print(
                "Spider wasn't fast enough | Connection Timed Out - Error Code : 1001-prior")
        except Exception as exec:
            print("An error occured while scraping data {}".format(exec))

        return driver
    
