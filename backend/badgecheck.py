#!/bin/env python3
import settings, logging, argparse, requests
from copy		import deepcopy
from datetime	import datetime
from uuid		import UUID
from os			import path, chdir


def getAttndViaBadgeNumber(num):
	if (type(num) != int) or num < 0:
		logger.warning('({}) is not an integer or is less than 0'.format(num))
		raise ValueError('')
	req = deepcopy(settings.magapi.lookup)
	req['params'][0] = str(num)
	resp = requests.post(
		getSetting('url'),
		json=req,
		headers=settings.magapi.headers
	)
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
		'-v', '--verbose', action='store_true',
		help='Output more verbose info')
	parser.add_argument(
		'--debug', action='store_true',
		help='Run with debug settings')
	return parser.parse_args()


def startup():
	chdir(path.dirname(path.abspath(__file__)))
	open(settings.logfile, 'w').close()

	# Set up logging
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	# Set loglevel and format
	ch.setLevel(logging.WARN)
	if args.verbose:	ch.setLevel(logging.INFO)
	if args.debug:		ch.setLevel(logging.DEBUG)
	ch.setFormatter(logging.Formatter("[%(levelname)8s] %(name)s: %(message)s"))
	logger.addHandler(ch)
	fh = logging.FileHandler(settings.logfile)
	# Set loglevel and format
	fh.setLevel(logging.INFO); fh.setFormatter(logging.Formatter(
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
	logger = logging.getLogger(__name__)
	args = parseargs()
	startup()
