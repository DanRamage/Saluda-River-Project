import sys
sys.path.append('../../commonfiles/python')

from mako.template import Template
from mako import exceptions as makoExceptions
import os
import logging.config
import ConfigParser
import json
from output_plugin import output_plugin

class voicemail_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)
    self.outfile = None

  def initialize_plugin(self, **kwargs):
    try:
      details = kwargs['details']
      self.outfile = details.get("output", "filename")

      return True
    except Exception as e:
      self.logger.exception(e)
    return False

  def emit(self, **kwargs):
    if self.logger:
      self.logger.debug("Starting emit for voicemail output.")
    try:
      with open(self.outfile, "w") as out_json:
        failed_sites = kwargs['failed_sites']
        sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")
        json_data = {
          'sampling_date': sample_date,
          'sites': []
        }
        if len(failed_sites):
          for site in failed_sites:
            wq_site = site['wq_site']
            json_data['sites'].append(wq_site.description)
        out_json.write(json.dumps(json_data))
    except (IOError, Exception) as e:
      self.logger.exception(e)
    if self.logger:
      self.logger.debug("Finished emit for voicemail output.")

