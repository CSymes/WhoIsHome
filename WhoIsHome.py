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
POLL_PERIOD = 10 # time to wait between device polls (in seconds)
DC_GRACE_PERIOD = 60 # time to wait after a disconnect before notifying on reconnect

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

	print(f'Starting monitoring with a poll interval of {POLL_PERIOD}s and debounce period of {DC_GRACE_PERIOD}s')
	print(f'Pushbullet is {"" if pushbullet else "un"}available')

	last_seen = {}
	legal_status = {} # latched status
	last_time = 0

	try:
		first_run = True # run some first-time map inits

		while True:

			# get current time
			cur_time = int(time.time())

			results = {}
			# Attempt to ping each person's device
			for person in people:
				result = subprocess.call([*CMD_PING.split(), people[person]], stdout=subprocess.DEVNULL) == 0

				# print(person, '—', result)
				results[person] = result

				if first_run:
					legal_status[person] = result
					last_seen[person] = cur_time if result else 0

			first_run = False # don't init other times around the loop


			# only proceed if the state is considered valid
			if (cur_time < last_time + STATE_TIMEOUT):
				# compare each person's current connection status to their last-known
				for person in results:
					# check if we've exceeded the disconnect grace period
					past_grace = cur_time > (last_seen[person] + DC_GRACE_PERIOD)

					# Check if connected since last poll
					if results[person] and past_grace:
						report_conn(person)
						legal_status[person] = True

					# check if disconnected since last poll
					elif not results[person] and past_grace and legal_status[person]:
						report_dc(person)
						legal_status[person] = False

			# set state for next run
			for (k, v) in results.items():
				if v:
					last_seen[k] = cur_time
			last_time = cur_time

			# sleep
			time.sleep(POLL_PERIOD)
	except KeyboardInterrupt:
		print(last_seen)
		return




# Send a Pushbullet notification that someone has arrived
def report_conn(name):
	print(int(time.time()), name, 'has connected to the network')
	if pushbullet:
		pushbullet.push_note('Home Arrival', f'{name} has connected to the network')

# I don't personally care about people disconnecting at this point
def report_dc(name):
	print(int(time.time()), name, 'has disconnected from the network')


if __name__ == '__main__':
	main()



### TODO
# save state to disk on exit / load on start
# minimum number of polls to wait before marking person as away (debounce)
# configurable to restrict notifications to only when you are at home
