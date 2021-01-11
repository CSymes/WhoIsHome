#!/usr/bin/python3

import platform
import subprocess
import configparser



CONFIG_FILE = 'people.ini'
CMD_PING_NIX = f'ping -c 1 -w2'
CMD_PING_WIN = f'ping -n 1 -w2000'
CMD_PING = CMD_PING_WIN if platform.system().lower() == 'windows' else CMD_PING_NIX


config = configparser.ConfigParser()
with open(CONFIG_FILE) as conf_file:
	config.read_file(conf_file)
people = config['People']


for person in people:
	result = subprocess.call([*CMD_PING.split(), people[person]], stdout=subprocess.DEVNULL) == 0

	print(person, '—', result)


