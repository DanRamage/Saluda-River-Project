import sys
sys.path.append('../../commonfiles/python')

from mako.template import Template
from mako import exceptions as makoExceptions
import os
import logging.config
import ConfigParser

from smtp_utils import smtpClass
from output_plugin import output_plugin

class email_output_plugin(output_plugin):
  def __init__(self):
    output_plugin.__init__(self)
    self.logger = logging.getLogger(__name__)


  def initialize_plugin(self, **kwargs):
    try:
      details = kwargs['details']
      ini_file = details.get("ResultsEmail", "ini_file")

      config_file = ConfigParser.RawConfigParser()
      config_file.read(ini_file)

      self.mailhost = config_file.get("email_output_plugin", "mailhost")
      self.mailport = config_file.get("email_output_plugin", "port")
      self.fromaddr = config_file.get("email_output_plugin", "fromaddr")
      self.toaddrs = config_file.get("email_output_plugin", "toaddrs").split(',')
      self.subject = config_file.get("email_output_plugin", "subject")
      self.user = config_file.get("email_output_plugin", "user")
      self.password = config_file.get("email_output_plugin", "password")
      self.result_out_directory = config_file.get("email_output_plugin", "results_directory")
      self.results_template = config_file.get("email_output_plugin", "results_template")
      #self.report_url = details.get("Settings", "report_url")

      return True
    except Exception as e:
      self.logger.exception(e)
    return False

  def emit(self, **kwargs):
    if self.logger:
      self.logger.debug("Starting emit for email output.")

    if len(kwargs['failed_sites']):
      try:
        mytemplate = Template(filename=self.results_template)
        sample_date = kwargs['sampling_date'].strftime("%Y-%m-%d")
        results_outfile = os.path.join(self.result_out_directory, "%s.html" % (sample_date))
        with open(results_outfile, "w") as result_file_obj:
          results_report = mytemplate.render(sampling_date=sample_date,
                                             failed_sites=kwargs['failed_sites'],
                                             feedback_email=kwargs['feedback_email'])
          result_file_obj.write(results_report)
      except TypeError,e:
        if self.logger:
          self.logger.exception(makoExceptions.text_error_template().render())
      except (IOError,AttributeError,Exception) as e:
        if self.logger:
          self.logger.exception(e)
      else:
        try:
          subject = self.subject % (sample_date)
          #Now send the email.
          smtp = smtpClass(host=self.mailhost,
                           user=self.user, password=self.password,
                           port=self.mailport,
                           use_tls=True)
          smtp.rcpt_to(self.toaddrs)
          smtp.from_addr(self.fromaddr)
          smtp.subject(subject)
          smtp.message(results_report)
          smtp.send(content_type="html")
        except Exception as e:
          if self.logger:
            self.logger.exception(e)
    if self.logger:
      self.logger.debug("Finished emit for email output.")

