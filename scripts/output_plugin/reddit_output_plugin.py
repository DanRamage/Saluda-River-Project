import sys

sys.path.append('../../commonfiles/python')
import os
import logging.config
import time
import praw
from datetime import datetime
from output_plugin import output_plugin
import configparser as ConfigParser


class reddit_output_plugin(output_plugin):
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

            self.client_id = config_file.get("reddit_output_plugin", "client_id")
            self.client_secret = config_file.get("reddit_output_plugin", "client_secret")
            self.username = config_file.get("reddit_output_plugin", "username")
            self.password = config_file.get("reddit_output_plugin", "password")
            self.useragent = config_file.get("reddit_output_plugin", "password")
            self.subreddits = config_file.get("reddit_output_plugin", "subreddits").split(',')
            return True
        except Exception as e:
            self.logger.exception(e)
        return False

    def emit(self, **kwargs):
        self.logger.debug("Starting emit for reddit output.")
        try:
            failed_sites = kwargs['failed_sites']
            sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")
            try:
                reddit = praw.Reddit(client_id=self.client_id,
                                     client_secret=self.client_secret,
                                     user_agent='MySCRiversBot',
                                     password=self.password,
                                     username=self.username)

                title = "Midlands River Coalition Results %s" % (sample_date)
                output_text_list = []
                for site in failed_sites:
                    wq_site = site['wq_site']
                    test_results = site['test_result']
                    output_text_list.append("* Site: %s %s shows elevated bacteria levels." % \
                                            (wq_site.name, wq_site.description))
                if len(output_text_list) == 0:
                    output_text_list.append("* No sites show elevated bacteria levels.")

                output_text_list.append("[My SC Rivers Website](https://howsmyscriver.org)")
                output_text_list.append("[My SC Rivers Twitter](https://twitter.com/myscriver)")
                output_text_list.append("[My SC Rivers Instagram](https://www.instagram.com/midlandsrivercoalition/)")
                output_text_list.append("[My SC Rivers BlueSky](https://bsky.app/profile/midlandsriver.bsky.social)")
                output_text_list.append("Auto posted by MySCRiversBot")
                output_text = '\n\n'.join(output_text_list)
                for sub in self.subreddits:
                    self.logger.debug("Submitting to %s subreddit: %s" % (output_text, sub))
                    subreddit = reddit.subreddit(sub)
                    subreddit.submit(title, selftext=output_text)

            except Exception as e:
                self.logger.exception(e)

        except Exception as e:
            self.logger.exception(e)

        self.logger.debug("Finished emit for reddit output.")
