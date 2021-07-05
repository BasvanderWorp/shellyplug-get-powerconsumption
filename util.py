'''
Util module
'''
import logging
import json

def read_config(config_filename):
    # read config_filename (json file)
    logger = logging.getLogger(__name__)
    try:
        with open(config_filename) as f:
            config = json.load(f)
    except FileNotFoundError:
        msg = "Config file '%s' not found" % config_filename
        logger.error(msg)
        raise
    except json.decoder.JSONDecodeError as err:
        msg = "Invalid format configuration file '%s'" % config_filename + \
              ', error: %s' % str(err)
        logger.error(msg)
        raise

    return config
