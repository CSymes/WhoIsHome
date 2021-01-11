#!/usr/bin/python3

import os
import json
import time
import platform
import subprocess
from pushbullet import Pushbullet
from configparser import ConfigParser



CONFIG_FILE = 'people.ini'
STATE_FILE = 'status'
PB_KEY_FILE = 'pushbullet.ini'

# if it's older than this, ignore any change in state
STATE_TIMEOUT = 60*60 # time to regard the state over (in seconds)

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



	results = {}
	# Attempt to ping each person's device
	for person in people:
		result = subprocess.call([*CMD_PING.split(), people[person]], stdout=subprocess.DEVNULL) == 0

		print(person, '—', result)
		results[person] = result


	# compare results to the last known statuses
	if os.path.isfile(STATE_FILE):
		try:
			with open(STATE_FILE) as state_file:
				last_state = json.load(state_file)
		except json.JSONDecodeError:
			last_state = {}

		# get current time
		cur_time = time.time()
		results[TIME_INDEX] = cur_time
		# get time we last checked status
		if (TIME_INDEX in last_state):
			last_time = last_state[TIME_INDEX]
		else:
			last_time = 0

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



	# save current state back to disk
	with open(STATE_FILE, 'w') as state_file:
		json.dump(results, state_file)


# Send a Pushbullet notification that someone has arrived
def report_conn(name):
	if pushbullet:
		pushbullet.push_note('Home Arrival', f'{name} has connected to the network')

# I don't personally care about people disconnecting at this point
def report_dc(name):
	pass


if __name__ == '__main__':
	main()


### TODO
# State timeout
# Scheduling / main loop in memory?
