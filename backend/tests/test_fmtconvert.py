import unittest
from datetime   import datetime
from util		import fmtconvert

class FmtConversions(unittest.TestCase):
	dummy_stripped	= dict(
		name = "Edward Richardson", badge = "RRU-28413", ribbon = "no ribbon",
		badge_t = "staff", badge_n = 765, hr_total = 30, hr_worked = 0
	)

	@unittest.expectedFailure
	def test_ToLocalStripped(self):
		self.assertEqual(fmtconvert.magapiToBasicAttendee(""), self.dummy_stripped)

	def test_BasicAttendeeToCSV(self):
		epoch = datetime(1970,1,1)
		with self.subTest():
			self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped),
				"1970-01-01 00:00:00,staff,765,Edward Richardson,0,30,no ribbon,")
		with self.subTest("Input Validation: Wrong type"):
			self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped, 3),
				"1970-01-01 00:00:00,staff,765,Edward Richardson,0,30,no ribbon,")
		with self.subTest("Input Validation"):
			self.assertEqual(
				fmtconvert.BasicAttendeeToCSV(epoch, self.dummy_stripped, False),
				"1970-01-01 00:00:00,staff,765,Edward Richardson,0,30,no ribbon,False")
