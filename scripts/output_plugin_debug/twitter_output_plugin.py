import sys
sys.path.append('../../commonfiles/python')

import logging.config
import twitter

from output_plugin import output_plugin


class twitter_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)


  def initialize_plugin(self, **kwargs):
    try:
      details = kwargs['details']
      self.consumer_key = details.get("Authentication", "consumer_key")
      self.consumer_secret = details.get("Authentication", "consumer_secret")
      self.access_token = details.get("Authentication", "access_token")
      self.access_token_secret = details.get("Authentication", "access_token_secret")
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

      """
      if len(failed_sites):
        for site in failed_sites:
          wq_site = site['wq_site']
          test_results = site['test_result']
          twit_api.PostUpdate("Sample Date: %s Site: %s %s shows elevated bacteria levels." %(sample_date, wq_site.name, wq_site.description))
      else:
        twit_api.PostUpdate("Sample Date: %s No sites show elevated bacteria levels." % (sample_date))
      """
    except Exception as e:
      self.logger.exception(e)

    self.logger.debug("Finished emit for twitter output.")

