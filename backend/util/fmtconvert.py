import logging, json

def magapiToBasicAttendee(verbose):
	return ""

def BasicAttendeeToCSV(date, attendee, allowed=""):
	return "{},{},{},{},{},{},{},{}".format(
		date.strftime("%Y-%m-%d %H:%M:%S"),
		attendee['badge_t'], attendee['badge_n'],
		attendee['name'],
		attendee['hr_worked'], attendee['hr_total'],
		attendee['ribbon'],
		allowed if type(allowed) == bool else ""
	)
