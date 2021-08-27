import sys

sys.path.append('../../commonfiles/python')
import os
import logging.config
import time
from datetime import datetime
from output_plugin import output_plugin
import configparser as ConfigParser
import uuid
from wq_sites import wq_sample_sites
from mako.template import Template
from mako import exceptions as makoExceptions

class georss:
    def __init__(self, **kwargs):
        self.title  = kwargs.get('title', '')
        self.link   = kwargs.get('link', '')
        self.id = kwargs.get('id', '')
        self.update_datetime = kwargs.get('update_datetime', '')
        self.summary = kwargs.get('summary', '')
        self.longitude = kwargs.get('longitude', -1.0)
        self.latitude = kwargs.get('latitude', -1.0)

class georss_output_plugin(output_plugin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.details = None

    def initialize_plugin(self, **kwargs):
        try:
            self.details = kwargs['details']
            self.ini_file = self.details.get('Settings', 'ini_file')

            self.output_directory = self.details.get('Template_Settings', 'output_directory')
            self.output_filename = self.details.get('Template_Settings', 'output_filename')
            self.template_file  = self.details.get('Template_Settings', 'template_file')
            self.title  = self.details.get('Template_Settings', 'title')
            self.subtitle  = self.details.get('Template_Settings', 'subtitle')
            self.site_url  = self.details.get('Template_Settings', 'site_url')
            self.author  = self.details.get('Template_Settings', 'author')
            self.author_email  = self.details.get('Template_Settings', 'author_email')

            return True
        except Exception as e:
            self.logger.exception(e)
        return False

    def emit(self, **kwargs):
        self.logger.debug("Starting emit for georss output.")
        try:
            failed_sites = kwargs['failed_sites']
            sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")
            config_file = ConfigParser.RawConfigParser()
            config_file.read(self.ini_file)
            boundaries_location_file = config_file.get('boundaries_settings', 'boundaries_file')
            sites_location_file = config_file.get('boundaries_settings', 'sample_sites')
            wq_sites = wq_sample_sites()
            wq_sites.load_sites(file_name=sites_location_file, boundary_file=boundaries_location_file)
            georss_recs = []
            for wq_site in wq_sites:
                rss_rec = georss(title=wq_site.name,
                                 link="https://howsmyscriver.org",
                                 id=uuid.uuid4(),
                                 update_datetime=sample_date,
                                 longitude=wq_site.object_geometry.x,
                                 latitude=wq_site.object_geometry.y
                                 )
                failed_found = False
                for failed_site in failed_sites:
                    if wq_site.name == failed_site['wq_site'].name:
                        failed_found = True
                        rss_rec.summary = "Site: %s %s shows elevated bacteria levels." % \
                                          (wq_site.name, wq_site.description)
                        break
                if not failed_found:
                    rss_rec.summary = "Site: %s %s shows no elevated bacteria levels." % \
                                      (wq_site.name, wq_site.description)

                georss_recs.append(rss_rec)

            try:
                mytemplate = Template(filename=self.template_file)
                results_outfile = os.path.join(self.output_directory, self.output_filename)
                with open(results_outfile, "w") as result_file_obj:
                    results_report = mytemplate.render(title=self.title,
                                                       subtitle=self.subtitle,
                                                       site_url=self.site_url,
                                                       update_datetime=sample_date,
                                                       author=self.author,
                                                       author_email=self.author_email,
                                                       main_id=uuid.uuid4(),
                                                       georss_recs=georss_recs)
                    result_file_obj.write(results_report)
            except TypeError as e:
                if self.logger:
                    self.logger.exception(makoExceptions.text_error_template().render())
            except (IOError, AttributeError, Exception) as e:
                if self.logger:
                    self.logger.exception(e)

        except Exception as e:
            self.logger.exception(e)

        self.logger.debug("Finished emit for georss output.")
