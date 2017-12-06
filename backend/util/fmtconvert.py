import logging, json
logging.basicConfig()
lgr = logging.getLogger(__name__)
lenDataTrunc = 30


def magapiToBasicAttendee(verbose):
	if type(verbose) != dict:
		# Input validation
		lgr.error(
			"Malformed data in conversion: {{:.{}}}"
			.format(lenDataTrunc)
			.format(str(verbose)) +
			(str() if (len(str(verbose)) < lenDataTrunc) else "...")
		)
		lgr.info("Data was:\n" + verbose)
		return dict()
	attnd = verbose['result']
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

