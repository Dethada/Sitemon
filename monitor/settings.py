"""
Settings for Web Monitor
"""
import logging
import os

LOG_LEVEL = logging.INFO

# Filename for log file
LOG_FILE = 'monitor.log'

logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=LOG_FILE,
                    filemode='a')

# File name for the sqlite3 database
DB_FILE = 'database.db'

# Seconds between reading data from the database
# Deafult 60 Seconds
CHECK_FREQUENCY = 1

# Seconds between each poll to the website
# Default 300 Seconds (5 mins)
POLL_FREQUENCY = 5

try:
    TELE_TOKEN = os.environ['TELE_TOKEN']
except KeyError:
    logging.error('No TELE_TOKEN not set as environment variable.')
    exit(1)
