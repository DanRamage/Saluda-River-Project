import sys
sys.path.append('../commonfiles/python')
import os
import logging.config
from datetime import datetime, timedelta
from pytz import timezone
import time
import optparse
import ConfigParser
import poplib
import email
from xlrd import xldate
import xlrd

from wq_sites import wq_sample_sites
from wq_output_results import wq_sample_data,wq_samples_collection,wq_advisories_file,wq_station_advisories_file

def check_email_for_update(config_filename):
  file_list = []
  logger = logging.getLogger('check_email_for_update_logger')
  logger.debug("Starting check_email_for_update")
  try:
    config_file = ConfigParser.RawConfigParser()
    config_file.read(config_filename)

    email_ini_config_filename = config_file.get("email_settings", "settings_ini")
    email_ini_config_file = ConfigParser.RawConfigParser()
    email_ini_config_file.read(email_ini_config_filename)

    email_host = email_ini_config_file.get("wq_results_email_settings", "host")
    email_user = email_ini_config_file.get("wq_results_email_settings", "user")
    email_password = email_ini_config_file.get("wq_results_email_settings", "password")
    destination_directory = email_ini_config_file.get("wq_results_email_settings", "destination_directory")
  except (ConfigParser.Error,Exception) as e:
    logger.exception(e)

  connected = False
  for attempt_cnt in range(0, 5):
    try:
      logger.info("Attempt: %d to connect to email server." % (attempt_cnt))

      pop3_obj = poplib.POP3_SSL(email_host, 995)
      pop3_obj.user(email_user)
      pop3_obj.pass_(email_password)
      connected = True
      logger.info("Successfully connected to email server.")
      break
    except (poplib.error_proto, Exception) as e:
      logger.exception(e)
      time.sleep(5)
  if connected:
    emails, total_bytes = pop3_obj.stat()
    for i in range(emails):
        # return in format: (response, ['line', ...], octets)
        response = pop3_obj.retr(i+1)
        raw_message = response[1]

        str_message = email.message_from_string("\n".join(raw_message))

        # save attach
        for part in str_message.walk():
          logger.debug("Content type: %s" % (part.get_content_type()))

          if part.get_content_maintype() == 'multipart':
            continue

          if part.get('Content-Disposition') is None:
            logger.debug("No content disposition")
            continue

          filename = part.get_filename()
          if filename.find('xlsx') != -1 or filename.find('xls'):
            download_time = datetime.now()
            logger.debug("Attached filename: %s" % (filename))
            save_file = "%s_%s" % (download_time.strftime("%Y-%m-%d_%H_%M_%S"), filename)
            saved_file_name = os.path.join(destination_directory, save_file)
            logger.debug("Saving file as filename: %s" % (saved_file_name))
            with open(saved_file_name, 'wb') as out_file:
              out_file.write(part.get_payload(decode=1))
              out_file.close()
              file_list.append(saved_file_name)

    #pop3_obj.quit()

  if logger:
    logger.debug("Finished check_email_for_update")
  return file_list

def parse_sheet_data(xl_file_name, wq_data_collection):
  logger = logging.getLogger('chs_historical_logger')
  logger.debug("Starting parse_sheet_data, parsing file: %s" % (xl_file_name))

  wb = xlrd.open_workbook(filename = xl_file_name)

  est_tz = timezone('US/Eastern')
  utc_tz = timezone('UTC')
  sample_date = None
  try:
    sheet = wb.sheet_by_name('Results')
  except Exception as e:
    logger.exception(e)
  else:
    row_headers = []
    results_ndx = None
    station_ndx = None
    date_ndx = None
    time_ndx = None
    for row_ndx,data_row in enumerate(sheet.get_rows()):
      if row_ndx != 0:
        try:
          wq_sample_rec = wq_sample_data()

          wq_sample_rec.station = data_row[station_ndx].value
          try:
            date_val = xlrd.xldate.xldate_as_datetime(data_row[date_ndx].value, wb.datemode)
          except Exception as e:
            date_val = datetime.strptime(data_row[date_ndx].value, "%Y-%m-%d")

          try:
            time_val = datetime.strptime(data_row[time_ndx].value, "%H%M")
          except Exception as e:
            val = data_row[date_ndx].value
            time_val = datetime.strptime(str(data_row[time_ndx].value), "%H%M")
          wq_sample_rec.date_time = (est_tz.localize(datetime.combine(date_val.date(), time_val.time()))).astimezone(utc_tz)
          wq_sample_rec.value = data_row[results_ndx].value
          logger.debug("Site: %s Date: %s Value: %s" % (wq_sample_rec.station,
                                                        wq_sample_rec.date_time,
                                                        wq_sample_rec.value))
          if sample_date is None or date_val > sample_date:
            sample_date = date_val
          wq_data_collection.append(wq_sample_rec)
        except Exception as e:
          logger.error("Error found on row: %d" % (row_ndx))
          logger.exception(e)
      else:
        #Copy the header names out
        for cell in data_row:
          row_headers.append(cell.value)
        station_ndx = row_headers.index('Station')
        date_ndx = row_headers.index('Date')
        time_ndx = row_headers.index('Time')
        results_ndx = row_headers.index('Result')

  return sample_date

def main():
  parser = optparse.OptionParser()
  parser.add_option("-c", "--ConfigFile", dest="config_file", default=None,
                    help="INI Configuration file." )

  (options, args) = parser.parse_args()

  if options.config_file is None:
    parser.print_help()
    sys.exit(-1)

  try:
    config_file = ConfigParser.RawConfigParser()
    config_file.read(options.config_file)
  except Exception, e:
    raise
  else:
    logger = None
    try:
      logConfFile = config_file.get('logging', 'config_file')
      boundaries_location_file = config_file.get('boundaries_settings', 'boundaries_file')
      sites_location_file = config_file.get('boundaries_settings', 'sample_sites')
      results_file = config_file.get('json_settings', 'advisory_results')
      station_results_directory = config_file.get('json_settings', 'station_results_directory')

      if logConfFile:
        logging.config.fileConfig(logConfFile)
        logger = logging.getLogger('sc_rivers_wq_data_harvest_logger')
        logger.info("Log file opened.")
    except ConfigParser.Error, e:
      if logger:
        logger.exception(e)
    else:
      wq_sites = wq_sample_sites()
      wq_sites.load_sites(file_name=sites_location_file, boundary_file=boundaries_location_file)

      wq_data_files = check_email_for_update(options.config_file)
      if logger is not None:
        logger.debug("Files: %s found" % (wq_data_files))

      wq_data_collection = wq_samples_collection()
      for wq_file in wq_data_files:
        parse_sheet_data(wq_file, wq_data_collection)
        if logger:
          logger.debug("Finished parse_sheet_data")

      #Create the geojson files
      current_advisories = wq_advisories_file(wq_sites)
      current_advisories.create_file(results_file, wq_data_collection)

      for site in wq_sites:
        site_advisories = wq_station_advisories_file(site)
        site_advisories.create_file(station_results_directory, wq_data_collection)
      if logger is not None:
        logger.info("Log file closed.")

  return

if __name__ == "__main__":
  main()
