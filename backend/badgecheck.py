#!/bin/env python3
import settings, logging, argparse, requests, asyncio
from copy		import deepcopy
from datetime	import datetime
from functools	import partial
from uuid		import UUID
from os			import path, chdir


async def getAttndFromBadge(badge):
	'''Takes a string that can be scanned barcode or a positive number,
	otherwise raises a ValueError, then queries the MAGAPI for the
	associated attendee'''
	if (type(badge) == str and [0] != '~'):
		req = deepcopy(settings.magapi.barcode_lookup)
	else:
		if int(badge) < 0:
			logger.warning('({}) is less than 0'.format(badge))
			raise ValueError('({}) is less than 0'.format(badge))
		req = deepcopy(settings.magapi.lookup)
	req['params'][0] = str(badge)
	kwargs = dict(
		url=getSetting('url'),
		timeout=getSetting('timeout'),
		json=req,
		headers=settings.magapi.headers
	)

	logger.info('Looking up badge {}'.format(badge))
	logger.debug(req)
	futr_resp = loop.run_in_executor(None, partial(requests.post, **kwargs))
	resp = await futr_resp
	logger.info('Server response was HTTP {}'.format(resp.status_code))
	logger.debug(resp.text)

	return resp


def getSetting(name):
	'''Get setting from either debug or runtime scope. If getting setting from
	debug scope, fall back to runtime scope if debug doesn't specify'''
	if args.debug:
		return getattr(settings.debug, name, getattr(settings.runtime, name))
	else:
		return getattr(settings.runtime, name)


def parseargs():
	'''Parses command-line arguments and returns them as a Namespace object'''
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-V', '--version', action='version',
		version="%(prog)s v{}".format(settings.version))
	parser.add_argument(
		'-e', '--expand-json', action='store_false', dest='minify',
		help='Add newlines and spacing to JSON responses')
	parser.add_argument(
		'-E', '--no-expand-json', action='store_true', dest='minify',
		help='Undo --expand-json')
	parser.add_argument(
		'-v', '--verbose', action='count', default=0,
		help='Output more verbose info. Specify more than once to increase.')
	parser.add_argument(
		'--debug', action='store_true',
		help='Run with debug settings')
	return parser.parse_args()


def startup():
	chdir(path.dirname(path.abspath(__file__)))
	open(settings.logfile, 'w').close()
	global args, logger
	args = parseargs()

	# Set up logging
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	# Set loglevel and format
	ch.setLevel(logging.WARN)
	if args.verbose > 0:
		ch.setLevel(logging.INFO)
	if args.verbose > 1:
		ch.setLevel(logging.DEBUG)
		logging.getLogger("requests").setLevel(logging.DEBUG)
		logging.getLogger("urllib3").setLevel(logging.DEBUG)
	ch.setFormatter(logging.Formatter("[%(levelname)8s] %(name)s: %(message)s"))
	logger.addHandler(ch)
	fh = logging.FileHandler(settings.logfile)
	# Set loglevel and format
	fh.setLevel(logging.INFO)
	fh.setFormatter(logging.Formatter(
		"%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
		"%Y-%m-%d %H:%M:%S"))
	logger.addHandler(fh)
	logger.debug('Logging set up.')
	logger.debug('Args state: {}'.format(args))
	logger.info('Badge check midlayer v{} starting on {} ({})'.format(
		settings.version,
		datetime.now().date(),
		datetime.now().date().strftime("%A")))

	# Set up API key
	try:
		with open('apikey.txt') as f:
			settings.magapi.headers['X-Auth-Token'] = str(UUID(f.read().strip()))
	except FileNotFoundError:
		logger.fatal('Could not find API key file, refusing to run.')
		raise SystemExit
	except ValueError:
		logger.fatal('API key not a valid UUID, refusing to run.')
		raise SystemExit


if __name__ == '__main__':
	startup()
