import os
import re

DATABASE_FILENAME = 'user-eng-db.cfg'
DATABASE_FILE = 'config/' + DATABASE_FILENAME
REMOTE_GIT_DB = 'https://github.com/aluriak/se-pioneers-db.git'
LOCAL_GIT_DIR = 'pioneers-db'
LOCAL_GIT_DB = os.path.join(LOCAL_GIT_DIR, DATABASE_FILENAME)
DIFFLIB_TO_HUMAN = {' ': 'unchanged', '+': 'added', '-': 'modified', '?': 'unexpected'}

REG_DATA_LOCATION = re.compile(r'LocName\s"([^"]+)"')
REG_DATA_NAME = re.compile(r'Name\s+"([^"]+)"')
REG_DATA_PIONEER = re.compile(r'Pioneer\s+"([^"]+)"')
REG_DATA_DATE = re.compile(r'Date\s+"([^"]+)"')
