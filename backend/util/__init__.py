from .improve import *
from .loggingfunctions import *
from logging import getLogger
import badgecheck
import util.state

logger = getLogger(__name__)
special_badges = [17800, 15098, 15097, 15099]
specialMSG = "{} is allowed to receive food regardless of meeting requirements."


def addResponseMessage(resp, message):
	if 'message' not in resp['result']:
		resp['result']['message'] = str(message)
	else:
		resp['result']['message'] += " " +str(message)


def specialBadgeCheck(resp):
	if resp['result']['badge_num'] in special_badges:
		addResponseMessage(
			resp,
			specialMSG.format(resp['result']['name'])
		)
