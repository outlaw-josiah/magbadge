import logging, os.path as path


logger = logging.getLogger(__name__)


def setLogLevel(level, firstRun=False):
	'''Sets logging level based on the program verbosity state. Only cares
	about the first StreamHandler or FileHandler attached to logger.
	Logging levels:
	0: Default. Only WARN+ are logged to console. File gets INFO+
		Sub-modules get only CRITICAL
	1: Console logs INFO+      4: Sub-modules log WARN+
	2: File/Con logs DEBUG+    5: Sub-modules log INFO+
	3: Sub-modules log ERROR+  6: Sub-modules log DEBUG+
	'''
	rootLogger = logging.getLogger()
	ch = [h for h in rootLogger.handlers if type(h) is logging.StreamHandler][0]
	fh = [h for h in rootLogger.handlers if type(h) is logging.FileHandler][0]
	if not firstRun:
		logger.warning("Changing log level")
	# Set to default levels
	ch.setLevel(logging.WARN)
	fh.setLevel(logging.INFO)
	logging.getLogger("requests").setLevel(logging.CRITICAL)
	logging.getLogger("urllib3").setLevel(logging.CRITICAL)
	logging.getLogger("websockets").setLevel(logging.CRITICAL)
	if level == 1:
		ch.setLevel(logging.INFO)
	if level >= 2:
		ch.setLevel(logging.DEBUG)
		fh.setLevel(logging.DEBUG)
	# Only bother if the level for these would be changed
	if level >= 3:
		if level == 3:
			level = logging.ERROR
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif level == 4:
			level = logging.WARN
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif level == 5:
			level = logging.INFO
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif level >= 6:
			level = logging.DEBUG
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)


def recordBadge(data, filename, now):
	'''Take simplified data and record it to CSV'''
	logger.debug('Logging to {}'.format(filename))
	line = (
		"{0}|{badge_num}|{name}|{dept_head}|{staff}|{hr_worked}|{hr_total}|"
		"{ribbons}\n".format(now, **data))
	if not path.isfile(filename):
		with open(filename, 'w') as file:
			file.write(
				"Time|Badge|Name|Dept Head|Staff|Worked hr|Total hr|Ribbons\n")
	with open(filename, 'a') as file:
		file.write(line)
