import sys
sys.path.append('../../commonfiles/python')
import os
import logging.config
if sys.version_info[0] < 3:
  import ConfigParser
else:
  import configparser as ConfigParser

import shutil
import time
from datetime import datetime
from PIL import Image
from output_plugin import output_plugin
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from instabot import Bot

class instagram_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)
    self.details = None

  def initialize_plugin(self, **kwargs):
    try:
      self.details = kwargs['details']

      self._instabot_directory = self.details.get("instagram_settings", "instagram_bot_base_path")
      self._tags = self.details.get("instagram_settings", "tags")
      ini_file = self.details.get("Authentication", "ini_file")

      config_file = ConfigParser.RawConfigParser()
      config_file.read(ini_file)
      self._username = config_file.get("instagram_plugin", "username")
      self._password = config_file.get("instagram_plugin", "password")
      return True
    except Exception as e:
      self.logger.exception(e)
    return False

  def emit(self, **kwargs):
    self.logger.debug("Starting emit for instagram output.")
    try:
      failed_sites = kwargs['failed_sites']
      sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")
      #We have to clear and then recreate the instagram working directory
      if os.path.exists(self._instabot_directory):
        shutil.rmtree(self._instabot_directory)
      #insta_bot = None
      insta_bot = Bot(base_path=self._instabot_directory)
      insta_bot.login(username=self._username, password=self._password)
      insta_message = []
      if len(failed_sites):

        for site in failed_sites:
          insta_message.append("Site: %s %s shows elevated bacteria levels." % (site['wq_site'].name, site['wq_site'].description))
          self.logger.debug("Sample Date: %s Site: %s %s shows elevated bacteria levels." % (sample_date, site['wq_site'].name, site['wq_site'].description))
      else:
        insta_message.append("No sites show elevated bacteria levels.")
        self.logger.debug("Sample Date: %s No sites show elevated bacteria levels." % (sample_date))

      insta_message.append(self._tags)
      self.create_screenshot(insta_bot, sample_date, insta_message)
    except Exception as e:
      self.logger.exception(e)

    self.logger.debug("Finished emit for instagram output.")

  def create_screenshot(self, insta_bot, sample_date, insta_message):
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
      insta_screenshot_filename = os.path.join(output_directory, "%s_instagram_sized.png" % (now_time.strftime("%Y_%m_%d_%H_%M")))
      self.logger.debug("Destination file: %s" % (screenshot_filename))
      driver.save_screenshot(screenshot_filename)

      logo_image = Image.open(logo_file, "r")
      small_logo = logo_image.resize((256,256))
      screenshot_image = Image.open(screenshot_filename, "r")
      screenshot_image.paste(small_logo, (10,45), mask=small_logo)
      #Instagram wants a 1080x1080 pic so let's resize.
      insta_size = (1080,608)
      insta_image = screenshot_image.resize(insta_size)
      self.logger.debug("Branded file: %s" % (screenshot_filename))
      combined_img_filename = os.path.join(output_directory, "%s_branded.png" % (now_time.strftime("%Y_%m_%d_%H_%M")))
      screenshot_image.save(combined_img_filename)

      insta_combined_img_filename = os.path.join(output_directory, "%s_insta_resized_branded.jpg" % (now_time.strftime("%Y_%m_%d_%H_%M")))
      self.logger.debug("Insta Branded file: %s" % (insta_combined_img_filename))
      insta_jpg = insta_image.convert('RGB')
      insta_jpg.save(insta_combined_img_filename)

      driver.quit()
      sites_message = "\n".join(insta_message)
      caption = ("%s\nSample Date: %s\n%s" % (url_to_screenshot,sample_date, sites_message))
      if insta_bot:
        if not insta_bot.upload_photo(insta_combined_img_filename, caption):
          self.logger.error("Error posting screenshot.")

      self.logger.debug("Screenshot finished in %f seconds" % (time.time()-start_time))
    except Exception as e:
      self.logger.exception(e)
    return