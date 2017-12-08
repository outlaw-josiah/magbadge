class runtime:
	url = "https://onsite.uber.magfest.org/uber/jsonrpc/"
	l_port = 28424
	logfile_pre = ""
	logfile_suf = ".csv"
	timeout = 2


class debug:
	"""Settings that should be used during debugging."""
	url = runtime.url.replace("onsite", "staging4")
	logfile_pre = "DEBUG_"
	timeout = 4


class magapi:
	"""Generic MAG API calls. These will error out if called as-is.
	Additionally contains the headers for calling the API (without auth token)"""
	headers = {
		"Content-Type": "application/json",
		"X-Auth-Token": ""}
	lookup = {
		"method": "attendee.lookup",
		"params": ["badge_num", "full"]}
	search = {
		"method": "attendee.search",
		"params": ["query"]}
	barcode_lookup = {
		"method": "barcode.lookup_attendee_from_barcode",
		"params": ["barcode_value", "full"]}
	barcode_badge = {
		"method": "barcode.lookup_badge_number_from_barcode",
		"params": ["barcode_value"]}


# Everything else here is "Hardcoded" settings, put here to keep them out of the
# main module
from distutils.version import StrictVersion
version = StrictVersion("2.0.0a1")
logfile = "server.log"
