# Import libraries
import requests
import getpass
from datetime import datetime, timedelta
import math
import json
import logging
import time
import os
import socket
import argparse
from util import read_config
from datetime import datetime

# =========================================================================
# === Part 0.1: Set global variables                                   ====
# =========================================================================
PROGRAM_NAME = 'read_shelly'
PROGRAM_VERSION = "0.11"
PROGRAM_VERSION_DATE = "08-07-2021"
PROGRAM_AUTHOR = "Bas van der Worp"
CONFIG_STORE = '/shelly/shelly_config.json'
CONFIG = read_config(CONFIG_STORE)
LOG_PATH_BASE = CONFIG['LOG_PATH_BASE']
OUTPUT_PATH_BASE = CONFIG['OUTPUT_PATH_BASE']
DEVICES = CONFIG['devices']
OUTFILE = 'c:/temp/outfile.log'
RETRY_TIME = 2

if __name__ == '__main__':
    # ========================================================================
    # === Part 0.2: Commandline parameter initialisation                  ====
    # ========================================================================
    # Parameter handling with argparse
    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-s", "--shellyplug_name", help="Shelly plug name",
                               required=True)
    args = parser.parse_args()

    if args.shellyplug_name:
        shellyplug_name = args.shellyplug_name
    else:
        shellyplug_name = ""

    # =========================================================================
    # === Part 0.3: Initialise logging                                     ====
    # =========================================================================
    # Check whether logfolder exists. If not, write to 'log' folder
    LOG_PATH = f'{LOG_PATH_BASE}{PROGRAM_NAME}/{shellyplug_name}/'
    if not os.path.exists(LOG_PATH):
        try:
            os.makedirs(LOG_PATH)
        except OSError as e:
            if e.errno != errno.EEXIST:
                LOG_PATH = ""
                raise

    OS_USER = os.getlogin().lower()
    LOGLEVEL_DEBUG = eval('logging.DEBUG')
    LOGLEVEL_INFO = eval('logging.INFO')

    LOGFILE = os.path.normpath(LOG_PATH + "log"
                               "_" + "{:%Y%m%d}".format(datetime.now()) +
                               ".log")

    logging.basicConfig(
        filename=LOGFILE,
        level='INFO',
        format='%(asctime)s %(levelname)s ' +
               '%(name)s %(funcName)s: %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S')
    logger = logging.getLogger(__name__)

    msg_1 = '='*80
    logger.info(msg_1)
    logger.info('Start program    : ' + PROGRAM_NAME)
    logger.info('Version          : ' + PROGRAM_VERSION)
    logger.info('Version date     : ' + PROGRAM_VERSION_DATE)
    logger.info('Host             : ' + socket.gethostname())
    logger.info('parameters       : ')
    logger.info(f'  Plug Name      : {str(shellyplug_name)}')


    # Get shelly device configuration
    # check if device exists
    if shellyplug_name not in DEVICES.keys():
        error_message = f"Shelly plug name '{shellyplug_name}' does not exist " + \
                        'in configuration'
        logger.error(error_message)
        raise ValueError(error_message)

    device_url = DEVICES[shellyplug_name]['DEVICE_URL']
    device_name = DEVICES[shellyplug_name]['DEVICE_NAME']
    username = DEVICES[shellyplug_name]['USERNAME']
    password = DEVICES[shellyplug_name]['PASSWORD']

    # Controleer of outputmap bestaat en anders aanmaken
    OUTPUT_PATH = f'{OUTPUT_PATH_BASE}/{device_name}/'
    if not os.path.exists(OUTPUT_PATH):
        try:
            os.makedirs(OUTPUT_PATH)
        except OSError as e:
            if e.errno != errno.EEXIST:
                OUTPUT_PATH = ""
                raise

    logger.info(f'Output path      : {OUTPUT_PATH}')

    # Set uri
    headers = {'User-Agent': 'curl/7.55.1'}

    # =========================================================================
    # === Part 1.0: Start polling and writing output                       ====
    # =========================================================================
    while True:
        time.sleep(0.5)
        try_number = 1
        success = False

        url = f'http://{device_url}/meter/0'

        while try_number < 10 and not success:
            try:
                result_bytes = requests.get(url, auth=(username,
                                                       password),
                                            headers=headers, timeout=5)
                success = True
            except requests.exceptions.Timeout:
                try_number += 1
                logger.warning(f'timeout error, retry {try_number}')
                time.sleep(RETRY_TIME)
                continue

            except requests.exceptions.ConnectionError as err:
                try_number += 1
                logger.warning(f'Error ConnectionError, retry ' + \
                               f'{try_number} in {RETRY_TIME} secs')
                time.sleep(RETRY_TIME)
                continue

            except requests.exceptions.NewConnectionError as err:
                try_number += 1
                logger.warning(f'Error NewConnectionError, retry ' + \
                               f'{try_number} in {RETRY_TIME} secs')
                time.sleep(RETRY_TIME)
                continue

        result_dict = eval(result_bytes.content.decode('utf-8').replace('true',
                                                                        'True'))
        power = result_dict['power']
        total = result_dict['total']
        timestamp = datetime.now()
        logline = f'{str(timestamp)};{power};{total}\n'

        now_datetime = datetime.now()
        datetime_now_min_str = now_datetime.strftime('%Y%m%d')
        OUTFILE = f'{OUTPUT_PATH}/{datetime_now_min_str}_output.csv'

        try:
            with open(OUTFILE, 'a') as outfile:
                outfile.write(logline)
        except:
            with open(OUTFILE, 'a+') as outfile:
                outfile.write(logline)
