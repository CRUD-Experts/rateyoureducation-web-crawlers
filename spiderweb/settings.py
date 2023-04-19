import datetime
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Remote
import os
import dotenv
dotenv.load_dotenv()

class ChromeSettings:
    def __init__(self,proxy = None,set_chrome_options = True):
        self.set_chrome_options = set_chrome_options
        self.proxy = "proxy:goes-here" 
    
    def _set_chrome_options(self) -> None:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        #chrome_options.add_argument('--proxy-server=%s' % self.proxy)
        chrome_prefs = {}
        chrome_options.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        return chrome_options

    def chef(self,url: str):
        """
        Establishes connection with hyperlinks
        Args:       
            url:str | url to scrape
            driver:webdriver object | an already existing driver which has knowledge of a pre-assigned url
        Returns:      
            soup:beautiful soup object
            driver:webdriver object           
            """
        #driver = webdriver.Chrome(chrome_options  = self._set_chrome_options(),options = ChromeDriverManager().install())#    \
                  # if self.set_chrome_options is True else  webdriver.Chrome()       #

        #driver = webdriver.Chrome()

        print(os.environ.get("SELENIUM_DRIVER_ENDPOINT"))
        
        driver = Remote(
        command_executor ="http://selenium-hub:4444/wd/hub",  # os.environ.get("SELENIUM_DRIVER_ENDPOINT") ,#'http://selenium:4444/wd/hub',
        desired_capabilities= {'browserName': 'chrome', 'javascriptEnabled': True,"enableVideo": True},
        options = self._set_chrome_options()
        )

        driver.get(url)
        try:
            WebDriverWait(
                driver, 10).until( 
                EC.presence_of_element_located(
                    (By.ID, "gs_bdy_ccl")))
        except TimeoutException as timeout:
                raise f"Spider wasn't fast enough | Connection Timed Out |{timeout}"
        except Exception as exec:
            raise "Spider failed to launch webpage{}".format(exec)
        else:
            return driver
    
