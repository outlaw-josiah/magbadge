import unittest
import logging
from datetime		import datetime
from util			import fmtconvert
from testfixtures	import log_capture

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
