import sys
sys.path.append('../../commonfiles/python')

import logging.config
import twitter
import ConfigParser

from output_plugin import output_plugin


class twitter_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)


  def initialize_plugin(self, **kwargs):
    try:
      details = kwargs['details']

      ini_file = details.get("Authentication", "ini_file")

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

    except Exception as e:
      self.logger.exception(e)

    self.logger.debug("Finished emit for twitter output.")

