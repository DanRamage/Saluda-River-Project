import sys
sys.path.append('../commonfiles/python')

import os
import optparse
import logging.config
import configparser
from datetime import datetime, timezone
import json
from xenia_obs_map import obs_map, json_obs_map
from xeniaSQLiteAlchemy import xeniaAlchemy as sl_xeniaAlchemy
from xeniaSQLiteAlchemy import multi_obs, platform
from wq_sites import wq_sample_sites
from wq_output_results import wq_sample_data,wq_samples_collection
from sqlalchemy.orm.exc import *
from sqlalchemy import exc

logger = logging.getLogger()

source_to_xenia = [
    {
        'header_column': 'enterococci',
        'source_uom': 'cfu',
        'target_obs': 'enterococci',
        'target_uom': 'cfu',
        's_order': 1
    }
]

def normalize_m_date(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat(sep=" ")

def save_to_database(sample_sites, wq_sample_recs, **kwargs):
    row_entry_date = datetime.now()

    if 'sqlite_file' in kwargs:
        sqlite_file = kwargs['sqlite_file']
        db_obj = sl_xeniaAlchemy()
        if db_obj.connectDB('sqlite', None, None, sqlite_file, None, False):
            logger.info("Succesfully connect to DB: %s" % (sqlite_file))
        else:
            logger.error("Unable to connect to DB: %s" % (sqlite_file))


    for site in wq_sample_recs:
        for sample_rec in wq_sample_recs[site]:
            site_rec = sample_sites.get_site(sample_rec.station)
            if site_rec:
                try:
                    platform_handle = f"mrc.{sample_rec.station}.sample_site"
                    longitude = site_rec.object_geometry.x
                    latitude = site_rec.object_geometry.y
                    # Verify the platform exists in DB.
                    if db_obj.platformExists(platform_handle) is None:
                        # def newPlatform(self, rowEntryDate, platformHandle, fixedLongitude, fixedLatitude, active=1, url="", description=""):
                        try:
                            row_entry_date = datetime.now()
                            longitude = longitude
                            latitude = latitude
                            db_obj.newPlatform(row_entry_date,
                                           platform_handle,
                                           longitude,
                                           latitude)
                        except Exception as e:
                            logger.exception(e)

                    obs_mapping = json_obs_map()
                    obs_mapping.load_json(source_to_xenia)
                    obs_mapping.build_db_mappings(platform_handle=platform_handle,
                                                  sqlite_database_file=sqlite_file,
                                                  add_missing=True)
                    obs_nfo = obs_mapping.get_rec_from_source_name('enterococci')

                    logger.debug(f"Adding Platform: {platform_handle} Date: {sample_rec.date_time} Value: {sample_rec.value}")
                    m_date = normalize_m_date(sample_rec.date_time)
                    db_rec=multi_obs(row_entry_date=row_entry_date,
                                     platform_handle=platform_handle,
                                     sensor_id=(obs_nfo.sensor_id),
                                     m_type_id=(obs_nfo.m_type_id),
                                     m_date=m_date,
                                     m_lon=longitude,
                                     m_lat=latitude,
                                     m_value=sample_rec.value
                                     )
                    try:
                        db_obj.session.add(db_rec)
                        db_obj.session.commit()
                    # Trying to add record that already exists.
                    except exc.IntegrityError as e:
                        db_obj.session.rollback()
                        logger.error(f"Record already exists, updating."
                                     f" Platform: {platform_handle} ({obs_nfo.m_type_id})({obs_nfo.sensor_id}) Date: {sample_rec.date_time} Value: {sample_rec.value}")
                        try:
                            updated = db_obj.session.query(multi_obs).filter(
                                multi_obs.platform_handle == platform_handle,
                                multi_obs.m_date == m_date,
                                multi_obs.m_type_id == obs_nfo.m_type_id,
                                multi_obs.sensor_id == obs_nfo.sensor_id
                            ).update({
                                multi_obs.m_value: db_rec.m_value,
                                multi_obs.m_lon: db_rec.m_lon,
                                multi_obs.m_lat: db_rec.m_lat,
                                multi_obs.row_update_date: datetime.now(),
                            }, synchronize_session=False)
                            logger.info(f"Updated {updated} rows")
                            db_obj.session.commit()
                        except Exception as e:
                            logger.exception(e)
                    except Exception as e:
                        logger.exception(e)

                    #db_obj.addRec(db_rec, True)
                except Exception as e:
                    logger.exception(e)
    return



def main():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--ConfigFile", dest="config_file",
                      help="INI Configuration file.")

    (options, args) = parser.parse_args()

    config_file = configparser.RawConfigParser()
    config_file.read(options.config_file)

    log_config_file = config_file.get('logging', 'config_file')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger()
    logger.info("Log file opened.")

    boundaries_location_file = config_file.get('boundaries_settings', 'boundaries_file')
    sites_location_file = config_file.get('boundaries_settings', 'sample_sites')
    wq_sites = wq_sample_sites()
    wq_sites.load_sites(file_name=sites_location_file, boundary_file=boundaries_location_file)

    sqlite_file = config_file.get('database', 'sqlite_file')

    station_json_files = config_file.get('json_settings', 'station_results_directory')
    station_files = os.listdir(station_json_files)
    #Build a wq_samples_collection to save to the database.
    for file in station_files:
        full_station_path = os.path.join(station_json_files, file)
        print(f"Open file: {file}")
        wq_samples = wq_samples_collection()
        try:
            with open(full_station_path, "r") as station_file_obj:
                json_obj = json.load(station_file_obj)
        except Exception as e:
            logger.exception(e)
        else:
            station = json_obj['properties']['station']
            beachadvisories = json_obj['properties']['test']['beachadvisories']

            platform_handle = f"mrc.{station}.sample_site"

            for sample_data in beachadvisories:
                wq_sample = wq_sample_data()
                wq_sample.station = station
                wq_sample.date_time = sample_data['date']
                wq_sample.value = sample_data['value'][0]
                wq_samples.append(wq_sample)
            save_to_database(wq_sites, wq_samples, sqlite_file=sqlite_file)
    return


if __name__ == "__main__":
    main()