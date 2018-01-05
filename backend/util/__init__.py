from .improve import *
from .loggingfunctions import *
from logging import getLogger
import badgecheck
import util.state

logger = getLogger(__name__)


def addResponseMessage(resp, message):
	if 'message' not in resp['result']:
		resp['result']['message'] = str(message)
	else:
		resp['result']['message'] += " " +str(message)
