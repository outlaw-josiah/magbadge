import logging
import collections
from datetime import timedelta

logged_scans = dict()
SmallScan = collections.namedtuple('SmallScan', ['time', 'name'])
grace = timedelta(seconds=30)


def add_scan(result, when, meal):
	'''Add a result to the logged scans

	Checks to see if this Attendee has been scanned already. If they have
	throw a ValueError after adding them to the list, but only if it's been
	longer than the grace period. Uses a namedtuple in the list for easy
	access to information when querying.
	'''
	date = str(when.date())
	bnum = result['badge_num']
	if not date in logged_scans:
		logged_scans[date] = dict()
	if not meal in logged_scans[date]:
		logged_scans[date][meal] = dict()
	if result['badge_num'] in logged_scans[date][meal]:
		logged_scans[date][meal][bnum] += [SmallScan(
			when,
			result['name']
		)]
		first_scan = logged_scans[date][meal][bnum][0]
		this_scan = logged_scans[date][meal][bnum][-1]
		if (this_scan.time - first_scan.time) > grace:
			raise ValueError(
				"Badge #{} was already scanned (first {} ago)".format(
					bnum,
					this_scan.time - first_scan.time
				),
				first_scan,
				this_scan
			)
	else:
		logged_scans[date][meal][bnum] = [SmallScan(
			when,
			result['name']
		)]
