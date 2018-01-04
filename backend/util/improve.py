import util
from copy		import deepcopy
from logging	import getLogger


restr_standard_lbls = ['No gluten', 'No nuts', 'No pork', 'Vegetarian/Vegan', ]
restr_sandwiches = ['None', 'Peanut Butter', ]
logger = getLogger(__name__)


def improve(resp):
	checkMissingRestrictions(resp)
	checkMissingSandwiches(resp)


def checkMissingRestrictions(resp):
	resp = deepcopy(resp)
	global restr_standard_lbls
	new_restr = [
		x for x in resp['result']['restrict'][1]
		if x not in restr_standard_lbls
	]
	if len(new_restr) > 0:
		logger.critical('New food restrictions: {}'.format(new_restr))
		restr_standard_lbls += new_restr


def checkMissingSandwiches(resp):
	resp = deepcopy(resp)
	global restr_sandwiches
	new_sandwich = [
		x for x in resp['result']['sandwich']
		if x not in restr_sandwiches
	]
	if len(new_sandwich) > 0:
		logger.critical('New sandwich: {}'.format(new_sandwich))
		restr_sandwiches += new_sandwich
