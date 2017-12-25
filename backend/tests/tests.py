import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import unittest, logging, sys, asyncio, random
import badgecheck as bdgchk
from unittest.mock	import MagicMock
from json			import loads
from datetime		import datetime
from util			import fmtconvert
from testfixtures	import log_capture
from argparse		import Namespace


class FmtConversions(unittest.TestCase):
	dummy_stripped	= dict(
		name="Edward Richardson", badge="RRU-28413", ribbon="no ribbon",
		badge_t="staff", badge_n=500, hr_total=30, hr_worked=0
	)

	@log_capture(level=logging.ERROR)
	def test_magapiToBasicAttendee(self, capture):
		with self.subTest("Input Validation"):
			self.assertEqual(fmtconvert.magapiToBasicAttendee("Bad input"), {})
		with self.subTest("Input Validation 2"):
			self.assertEqual(fmtconvert.magapiToBasicAttendee(
				"Bad input long text 12345678901234567890"), {})
		capture.check(
			("util.fmtconvert", "ERROR",
			"Malformed data in conversion: Bad input"),
			("util.fmtconvert", "ERROR",
			"Malformed data in conversion: Bad input long text 1234567890..."))

	def test_BasicAttendeeToCSV(self):
		epoch = datetime(1970, 1, 1)
		compstr = "1970-01-01 00:00:00,staff,500,Edward Richardson,0,30,no ribbon,"
		with self.subTest(): self.assertEqual(
			fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped),
			compstr)
		with self.subTest("Input Validation: Wrong type"): self.assertEqual(
			fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped, 3),
			compstr)
		with self.subTest("Input Validation"): self.assertEqual(
			fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped, False),
			compstr + "False")

	# Doing this test just in case. Should never fail.
	def test_datetime_strftime(self):
		self.assertEqual(
			datetime(1970, 1, 1).strftime("%Y-%m-%d %H:%M:%S"),
			"1970-01-01 00:00:00")


class requestchecks(unittest.TestCase):
	bnums = [10**x for x in range(0, 4)] + [x for x in range(20, 41)]
	barcodes = [
		"~R3FsDQ", "~IyWvWg", "~o3aPCw", "~RCYmuw", "~IQY/Vw", "~FqrOLA", "~Mf8CUA", "~OncJ2A",
		"~fIdHsA", "~ye1h3g", "~rH4oQQ", "~7NDK/Q", "~CG5CMA", "~5KzC3g", "~TBFnbA", "~ZqD5ew",
		"~vM3AZw", "~D/0JmQ", "~Ef3y6Q", "~nE1GAw", "~jubaeA"]
	@classmethod
	def setUpClass(self):
		self.maxDiff = None
		bdgchk.logger = MagicMock(spec=logging.getLogger())
		bdgchk.args = Namespace(verbose=0, minify=True, debug=True)
		self.loop = asyncio.get_event_loop()
		bdgchk.loop = self.loop
		with open('apikey.txt') as f:
			bdgchk.settings.magapi.headers['X-Auth-Token'] = f.read().strip()

	@classmethod
	def tearDownClass(self):
		bdgchk.logger = None
		bdgchk.args = None
		bdgchk.settings.magapi.headers['X-Auth-Token'] = ''

	def test_viaBadgeNum(self):
		for b in random.sample(self.bnums,3):
			with \
			self.subTest("Badge {}".format(b)), \
			open('tests/sampledata/b{}.json'.format(b)) as f:
				apidata = self.loop.run_until_complete(
					bdgchk.getAttndFromBadge(b)).text
				sampledata = f.read()
				self.assertEqual(loads(apidata), loads(sampledata))

	def test_viaScannedBadge(self):
		for b in random.sample(self.bnums[4:],3):
			with \
			self.subTest("Badge {}".format(self.barcodes[b - 20])),\
			open('tests/sampledata/b{}.json'.format(b)) as f:
				apidata = self.loop.run_until_complete(
					bdgchk.getAttndFromBadge(self.barcodes[b - 20])).text
				sampledata = f.read()
				self.assertEqual(loads(apidata), loads(sampledata))

	def test_badString(self):
		with self.assertRaises(ValueError) as context:
			self.loop.run_until_complete(bdgchk.getAttndFromBadge("AAA"))
		self.assertIn(
			'Not a valid badge string',
			context.exception.args)

	def test_emptyString(self):
		with self.assertRaises(ValueError) as context:
			self.loop.run_until_complete(bdgchk.getAttndFromBadge(""))
		self.assertIn(
			'Not a valid badge string',
			context.exception.args)

	def test_badInt(self):
		with self.assertRaises(ValueError) as context:
			self.loop.run_until_complete(bdgchk.getAttndFromBadge(-1))
		self.assertIn(
			'(-1) is less than 0',
			context.exception.args)

	def test_badData(self):
		with self.assertRaises(ValueError) as context:
			self.loop.run_until_complete(bdgchk.getAttndFromBadge({}))
		self.assertIn(
			'Data was not an integer or a string',
			context.exception.args)

	def test_timeout(self):
		bdgchk.logger.error.reset_mock()
		bdgchk.requests.post = MagicMock(
			side_effect=bdgchk.requests.exceptions.ConnectTimeout())

		expected = bdgchk.requests.Response()
		expected.status_code = 598
		expected.error = 'Connection timed out after {}ms'.format(
			bdgchk.getSetting('timeout') * 1000)
		actual = self.loop.run_until_complete(bdgchk.getAttndFromBadge(1))

		self.assertEqual(expected.error, actual.error)
		self.assertEqual(expected.status_code, actual.status_code)
		bdgchk.logger.error.assert_called_once_with(
			'Connection timed out after {}ms'.format(
				bdgchk.getSetting('timeout') * 1000))

	def test_connectionError(self):
		bdgchk.logger.error.reset_mock()
		ce = bdgchk.requests.exceptions.ConnectionError('')
		ce.request = bdgchk.requests.Request()
		bdgchk.requests.post = MagicMock(side_effect=ce)

		expected = bdgchk.requests.Response()
		expected.status_code = 504
		expected.error = ''
		actual = self.loop.run_until_complete(bdgchk.getAttndFromBadge(1))

		self.assertEqual(expected.error, actual.error)
		self.assertEqual(expected.status_code, actual.status_code)
		bdgchk.logger.error.assert_called_once_with(
			'Failed to connect to None \nHeader: {}\nError: ')


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

if __name__ == '__main__':
	unittest.main()
