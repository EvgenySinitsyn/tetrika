"""
config
"""
import os
import sys
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv('config.env'))


try:
    CONFIG = {
        'mysql_base': os.environ['MYSQL_DATABASE'],
        'mysql_user': os.environ['MYSQL_ROOT_USER'],
        'mysql_password': os.environ['MYSQL_PASSWORD'],
        'mysql_charset': os.environ['CHARSRET'],
        'mysql_name_host': os.environ['MYSQL_NAME_HOST'],
        'mysql_port': int(os.environ['MYSQL_PORT']),
    }

    if CONFIG['mysql_user'] == 'root':
        CONFIG['mysql_password'] = os.environ['MYSQL_ROOT_PASSWORD']

except KeyError as error:
    print('KeyError: {}'.format(error))
    sys.exit(-1)
