import unittest, logging, badgecheck as bdgchk, sys, asyncio
from json			import loads
from datetime		import datetime
from util			import fmtconvert
from testfixtures	import log_capture
from argparse		import Namespace

class FmtConversions(unittest.TestCase):
	dummy_stripped	= dict(
		name = "Edward Richardson", badge = "RRU-28413", ribbon = "no ribbon",
		badge_t = "staff", badge_n = 500, hr_total = 30, hr_worked = 0
	)

#	@unittest.expectedFailure
	@log_capture(level=logging.ERROR)
	def test_magapiToBasicAttendee(self, capture):
		with self.subTest("Input Validation"):
			self.assertEqual(fmtconvert.magapiToBasicAttendee("Bad input"), {})
		with self.subTest("Input Validation 2"):
			self.assertEqual(fmtconvert.magapiToBasicAttendee(
				"Bad input long text 12345678901234567890"), {})
		capture.check(
			("util.fmtconvert","ERROR",
			"Malformed data in conversion: Bad input"),
			("util.fmtconvert","ERROR",
			"Malformed data in conversion: Bad input long text 1234567890..."))

	def test_BasicAttendeeToCSV(self):
		epoch = datetime(1970,1,1)
		compstr = "1970-01-01 00:00:00,staff,500,Edward Richardson,0,30,no ribbon,"
		with self.subTest():self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped),
				compstr)
		with self.subTest("Input Validation: Wrong type"):self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped,3),
				compstr)
		with self.subTest("Input Validation"):self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped, False),
				compstr + "False")

	# Doing this test just in case. Should never fail.
	def test_datetime_strftime (self):self.assertEqual(
			datetime(1970,1,1).strftime("%Y-%m-%d %H:%M:%S"),
			"1970-01-01 00:00:00")

class requestchecks(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		bdgchk.logger = logging.getLogger()
		bdgchk.args = Namespace(verbose=0, minify=True, debug=True)
		bdgchk.loop = asyncio.get_event_loop()
		with open('apikey.txt') as f:
			bdgchk.settings.magapi.headers['X-Auth-Token'] = f.read().strip()


	@classmethod
	def tearDownClass(cls):
		bdgchk.logger = None
		bdgchk.args = None
		bdgchk.settings.magapi.headers['X-Auth-Token'] = ''


	def test_viaBadgeNum(self):
		for b in ([10**x for x in range(0,4)] + [x for x in range(20,40)]):
			with self.subTest("Badge {}".format(b)), open('tests/sampledata/b{}.json'.format(b)) as f:
				apidata = bdgchk.loop.run_until_complete(bdgchk.getAttndFromBadge(b)).text
				sampledata = f.read()
				self.assertEqual(loads(apidata), loads(sampledata))


	def test_viaScannedBadge(self):
		self.maxDiff = None
		barcodes = [
			"~R3FsDQ", "~IyWvWg", "~o3aPCw", "~RCYmuw", "~IQY/Vw", "~FqrOLA", "~Mf8CUA", "~OncJ2A",
			"~fIdHsA", "~ye1h3g", "~rH4oQQ", "~7NDK/Q", "~CG5CMA", "~5KzC3g", "~TBFnbA", "~ZqD5ew",
			"~vM3AZw", "~D/0JmQ", "~Ef3y6Q", "~nE1GAw", "~jubaeA"]
		for b in [x for x in range(20,40)]:
			with \
			self.subTest("Badge {}".format(barcodes[b - 20])),\
			open('tests/sampledata/b{}.json'.format(b)) as f:
				apidata = bdgchk.loop.run_until_complete(bdgchk.getAttndFromBadge(barcodes[b - 20])).text
				sampledata = f.read()
				self.assertEqual(loads(apidata), loads(sampledata))


class testSettings(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		bdgchk.args = Namespace(debug=False)


	def test_runtime_gets(self):
		bdgchk.args.debug = False
		self.assertEqual(
			bdgchk.settings.runtime.url,
			bdgchk.getSetting('url'))
		self.assertEqual(
			bdgchk.settings.runtime.l_port,
			bdgchk.getSetting('l_port'))
		self.assertEqual(
			bdgchk.settings.runtime.logfile_suf,
			bdgchk.getSetting('logfile_suf'))


	def test_debug_gets(self):
		bdgchk.args.debug = True
		self.assertNotEqual(
			bdgchk.settings.runtime.url,
			bdgchk.getSetting('url'))
		self.assertEqual(
			bdgchk.settings.debug.url,
			bdgchk.getSetting('url'))
		self.assertEqual(
			bdgchk.settings.runtime.l_port,
			bdgchk.getSetting('l_port'))
		self.assertEqual(
			bdgchk.settings.runtime.logfile_suf,
			bdgchk.getSetting('logfile_suf'))
