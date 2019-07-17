import sys
sys.path.append('../../commonfiles/python')
import os
import logging.config
import twitter
import ConfigParser
import time
from datetime import datetime
from PIL import Image
from output_plugin import output_plugin
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class twitter_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)
    self.details = None

  def initialize_plugin(self, **kwargs):
    try:
      self.details = kwargs['details']

      ini_file = self.details.get("Authentication", "ini_file")

      config_file = ConfigParser.RawConfigParser()
      config_file.read(ini_file)

      self.consumer_key = config_file.get("twitter_output_plugin", "consumer_key")
      self.consumer_secret = config_file.get("twitter_output_plugin", "consumer_secret")
      self.access_token = config_file.get("twitter_output_plugin", "access_token")
      self.access_token_secret = config_file.get("twitter_output_plugin", "access_token_secret")
      return True
    except Exception as e:
      self.logger.exception(e)
    return False

  def emit(self, **kwargs):
    self.logger.debug("Starting emit for twitter output.")
    try:
      twit_api = twitter.Api(consumer_key=self.consumer_key,
                        consumer_secret=self.consumer_secret,
                        access_token_key=self.access_token,
                        access_token_secret=self.access_token_secret)
      self.logger.debug(twit_api.VerifyCredentials())
      failed_sites = kwargs['failed_sites']
      sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")


      if len(failed_sites):
        for site in failed_sites:
          wq_site = site['wq_site']
          test_results = site['test_result']
          #twit_api.PostUpdate("Sample Date: %s Site: %s %s shows elevated bacteria levels." %(sample_date, wq_site.name, wq_site.description))
          self.logger.debug("Sample Date: %s Site: %s %s shows elevated bacteria levels." %(sample_date, wq_site.name, wq_site.description))
      else:
        self.logger.debug("Sample Date: %s No sites show elevated bacteria levels." % (sample_date))
        #twit_api.PostUpdate("Sample Date: %s No sites show elevated bacteria levels." % (sample_date))

      self.create_screenshot(twit_api, sample_date)
    except Exception as e:
      self.logger.exception(e)

    self.logger.debug("Finished emit for twitter output.")

  def create_screenshot(self, twit_api, sample_date):
    try:
      start_time = time.time()

      url_to_screenshot = self.details.get("screenshot_settings", "url_to_screenshot")
      output_directory = self.details.get("screenshot_settings", "output_directory")
      logo_file = self.details.get("screenshot_settings", "logo_file")
      firefox_binary = self.details.get("screenshot_settings", "firefox_binary")
      geckodriver_binary = self.details.get("screenshot_settings", "geckodriver_binary")

      #We use the options to tell the webdriver to run Firefox headless(don't start a UI)
      options = Options()
      options.headless = True
      now_time = datetime.now()

      driver = webdriver.Firefox(options=options, firefox_binary=firefox_binary, executable_path=geckodriver_binary)
      driver.get(url_to_screenshot)
      #To make sure everything has rendered, we wait to see that the element ID on the page, "latest_sample", is there.
      WebDriverWait(driver, 30).until(lambda x: x.find_element_by_id("latest_sample"))
      screenshot_filename = os.path.join(output_directory, "%s.png" % (now_time.strftime("%Y_%m_%d_%H_%M")))
      self.logger.debug("Destination file: %s" % (screenshot_filename))
      driver.save_screenshot(screenshot_filename)

      logo_image = Image.open(logo_file, "r")
      small_logo = logo_image.resize((256,256))
      screenshot_image = Image.open(screenshot_filename, "r")
      screenshot_image.paste(small_logo, (10,45), mask=small_logo)
      self.logger.debug("Branded file: %s" % (screenshot_filename))
      combined_img_filename = os.path.join(output_directory, "%s_branded.png" % (now_time.strftime("%Y_%m_%d_%H_%M")))
      screenshot_image.save(combined_img_filename)
      driver.quit()
      tweet_text = ("Sample Date: %s\n%s" % (sample_date, url_to_screenshot))
      twit_api.PostUpdate(tweet_text, media=combined_img_filename)

      self.logger.debug("Screenshot finished in %f seconds" % (time.time()-start_time))
    except Exception as e:
      self.logger.exception(e)
    return