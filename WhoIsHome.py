#!/usr/bin/python3

import os
import time
import platform
import subprocess
from pushbullet import Pushbullet
from configparser import ConfigParser



CONFIG_FILE = 'people.ini'
PB_KEY_FILE = 'pushbullet.ini'

# if it's older than this, ignore any change in state
STATE_TIMEOUT = 5*60 # time to regard the state over (in seconds)
POLL_PERIOD = 5 # time to wait between device polls (in seconds)

PING_TIMEOUT = 2 # Timeout for pinging devices (in seconds)
CMD_PING_NIX = f'ping -c 1 -w{PING_TIMEOUT}' # ping command on general unix based systems
CMD_PING_WIN = f'ping -n 1 -w{PING_TIMEOUT * 1000}' # windows variant
# the required command
CMD_PING = CMD_PING_WIN if platform.system().lower() == 'windows' else CMD_PING_NIX


# Attempt to load a Pushbullet API key and initialise the API interface
pushbullet = None
with open(PB_KEY_FILE) as pb_file:
	pb_ini = ConfigParser()
	pb_ini.read_file(pb_file)
	pushbullet = Pushbullet(pb_ini['API']['key'])



def main():
	# Read the hostname or IPs from the config file
	config = ConfigParser()
	config.optionxform = str # preserve case on the names

	with open(CONFIG_FILE) as conf_file:
		config.read_file(conf_file)
	people = config['People']

	last_state = {}
	last_time = 0

	try:
		while True:

			results = {}
			# Attempt to ping each person's device
			for person in people:
				result = subprocess.call([*CMD_PING.split(), people[person]], stdout=subprocess.DEVNULL) == 0

				# print(person, '—', result)
				results[person] = result


			# get current time
			cur_time = time.time()

			# only proceed if the state is considered valid
			if (cur_time < last_time + STATE_TIMEOUT):
				# compare each person's current connection status to their last-known
				for person in results:
					if person in last_state: # check they have a last-seen status
						# Check if connected since last poll
						if results[person] > last_state[person]:
							report_conn(person)
						# check if disconnected since last poll
						elif results[person] < last_state[person]:
							report_dc(person)

			# set state for next run
			last_state = results
			last_time = cur_time

			# sleep
			time.sleep(POLL_PERIOD)
	except KeyboardInterrupt:
		# TODO save state to disk on exit / load on start
		print(last_time)
		print(last_state)
		return




# Send a Pushbullet notification that someone has arrived
def report_conn(name):
	print(name, 'has connected to the network')
	if pushbullet:
		pushbullet.push_note('Home Arrival', f'{name} has connected to the network')

# I don't personally care about people disconnecting at this point
def report_dc(name):
	print(name, 'has disconnected from the network')


if __name__ == '__main__':
	main()
