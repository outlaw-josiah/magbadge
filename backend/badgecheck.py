#!/bin/env python3
import settings, logging, argparse, requests, asyncio, websockets, json, signal
import textwrap
from copy		import deepcopy
from datetime	import datetime
from functools	import partial
from uuid		import UUID
from os			import path, chdir as _chdir
# Exceptions
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectTimeout, ConnectionError
from websockets.exceptions import ConnectionClosed


async def getAttndFromBadge(badge):
	'''Takes a string that can be scanned barcode or a positive number,
	otherwise raises a ValueError, then queries the MAGAPI for the
	associated attendee'''
	if type(badge) == str:
		if len(badge) == 0 or badge[0] != '~':
			logger.error('({}) is not a valid badge string'.format(badge))
			raise ValueError('Not a valid badge string', badge)
		req = deepcopy(settings.magapi.barcode_lookup)
	elif type(badge) == int:
		if int(badge) < 0:
			logger.error('({}) is less than 0'.format(badge))
			raise ValueError('({}) is less than 0'.format(badge))
		req = deepcopy(settings.magapi.lookup)
	else:
		logger.error('({}) not an integer or a string'.format(badge))
		raise ValueError('Data was not an integer or a string', badge)
	req['params'][0] = str(badge)
	kwargs = dict(
		url=getSetting('url'),
		timeout=getSetting('timeout'),
		json=req,
		headers=settings.magapi.headers
	)

	logger.info('Looking up badge {}'.format(badge))
	logger.debug(req)
	try:
		futr_resp = loop.run_in_executor(None, partial(requests.post, **kwargs))
		resp = await futr_resp
	except ConnectTimeout:
		resp = requests.Response()
		resp.status_code = 598
		resp.error = 'Connection timed out after {}ms'.format(
			getSetting('timeout') * 1000)
		logger.error(
			'Connection timed out after {}ms'.format(getSetting('timeout') * 1000))
		return resp
	except ConnectionError as e:
		resp = requests.Response()
		resp.status_code = 504
		resp.error = e.args[0]
		logger.error(
			'Failed to connect to {} \n'
			'Header: {}\n'
			'Error: {}'.format(
				e.request.url,
				e.request.headers,
				e.args[0]
			)
		)
		return resp
	except Exception as e:
		resp = requests.Response()
		resp.status_code = 500
		logger.critical(e)
		return resp
	logger.info('Server response was HTTP {}'.format(resp.status_code))
	logger.debug(resp.text)

	return resp


async def prcsConnection(sock, path):
	'''Process incoming connections'''
	logger.debug(
		'Client connection opened at {}:{}'.format(*sock.remote_address))
	try:
		while sock.open:
			msg = await sock.recv()
			resp = deepcopy(settings.generic_resp)
			try: msgJSON = json.loads(msg)
			except JSONDecodeError as e:
				logger.error(
					'Failed to decode: \n'
					'{}\n{}'.format(
						textwrap.fill(msg, **settings.textwrap_conf),
						textwrap.fill(e.args[0], **settings.textwrap_conf)
					))
				resp['status'] = 400
				resp['error'] = settings.error.JSON_invalid
				await sock.send(json.dumps(resp))
				sock.close()
				continue
			if type(msgJSON) != dict:
				logger.error(
					'JSON did not decode to a dict: \n'
					'{}'.format(
						textwrap.fill(msg, **settings.textwrap_conf)
					))
				resp['status'] = 400
				resp['error'] = settings.error.JSON_invalid
				await sock.send(json.dumps(resp))
				continue
			elif 'action' not in msgJSON:
				logger.error('JSON did not include action: {}'.format(msg))
				resp['status'] = 400
				resp['error'] = settings.error.JSON_NOOP
				await sock.send(json.dumps(resp))
				continue
			elif msgJSON['action'] == 'admin':
				pass
			elif msgJSON['action'] == 'query.badge':
				await getBadge(sock, msgJSON['params'], resp)
				continue
			elif msgJSON['action'] == 'query.state':
				pass
			elif msgJSON['action'] == 'echo':
				logger.warning(
					'Echo request for data on connection {1}:{2}\n'
					'{0}'.format(
						textwrap.fill(msg, **settings.textwrap_conf),
						*sock.remote_address
					))
				resp['status'] = 200
				resp['result'] = msgJSON
				await sock.send(json.dumps(resp))
			else:
				await sock.send("")
	except ConnectionClosed:
		logger.debug(
			'Connection {}:{} closed by client'.format(*sock.remote_address))


async def getBadge(sock, badge, resp):
	try: data = await getAttndFromBadge(badge)
	except ValueError as e:
		resp['status'] = 400
		resp['error'] = e.args
		await sock.send(json.dumps(resp))
		return
	if not data.ok or hasattr(data, 'error'):
		resp['status'] = 500 if data.ok else data.status_code
		resp['error'] = getattr(data, 'error', 'Unknown error')
		await sock.send(json.dumps(resp))
		return
	dataJSON = data.json()['result']
	if 'error' in dataJSON:
		resp['status'] = 400
		resp['error'] = dataJSON['error']
		await sock.send(json.dumps(resp))
		return
	resp['result'] = data.text
	await sock.send(json.dumps(resp))


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
		version="%(prog)s v{}".format(settings.version_full))
	parser.add_argument(
		'-e', '--expand-json', action='store_false', dest='minify',
		help='Add newlines and spacing to JSON responses')
	parser.add_argument(
		'-E', '--no-expand-json', action='store_true', dest='minify',
		help='Undo --expand-json')
	parser.add_argument(
		'-v', action='count', default=0, dest='verbose',
		help='Output more verbose info. Specify more than once to increase.')
	parser.add_argument(
		'--verbose', action='store', default=0, type=int, metavar='N',
		help='Specify verbosity level explicitly. Set level to N.')
	parser.add_argument(
		'--debug', action='store_true',
		help='Run with debug settings')
	return parser.parse_args()


def setLogLevel(firstRun=False):
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
	if args.verbose == 1:
		ch.setLevel(logging.INFO)
	if args.verbose >= 2:
		ch.setLevel(logging.DEBUG)
		fh.setLevel(logging.DEBUG)
	# Only bother if the level for these would be changed
	if args.verbose >= 3:
		if args.verbose == 3:
			level = logging.ERROR
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif args.verbose == 4:
			level = logging.WARN
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif args.verbose == 5:
			level = logging.INFO
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)
		elif args.verbose >= 6:
			level = logging.DEBUG
			logging.getLogger("requests").setLevel(level)
			logging.getLogger("urllib3").setLevel(level)
			logging.getLogger("websockets").setLevel(level)


def startup():
	'''Do basic setup for the program. This really should only be run once
	but has some basic tests to prevent double-assignment'''
	_chdir(path.dirname(path.abspath(__file__)))
	global args, logger, loop
	args = parseargs()
	loop = asyncio.get_event_loop()

	# Set up logging
	open(settings.logfile, 'w').close()
	conFmt = "[%(levelname)8s] %(name)s: %(message)s"
	filFmt = "[%(levelname)8s] %(asctime)s %(name)s: %(message)s"
	logger = logging.getLogger(__name__)
	rootLogger = logging.getLogger()
	if len(rootLogger.handlers) is 0:
		rootLogger.setLevel(logging.DEBUG)
		ch = logging.StreamHandler()
		ch.setFormatter(logging.Formatter(conFmt))
		fh = logging.FileHandler(settings.logfile)
		rootLogger.addHandler(ch)
		fh.setFormatter(logging.Formatter(filFmt, "%b-%d %H:%M:%S"))
		rootLogger.addHandler(fh)
		setLogLevel(True)
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

	global server
	try:
		server
	except NameError:
		server = loop.run_until_complete(websockets.serve(
			prcsConnection,
			'localhost',
			getSetting('l_port')))
		logger.info('Now listening for connections on {}:{}'.format(
			'localhost',
			getSetting('l_port')))


def sigint(signum, stack):
	print()
	logger.critical('Shutting down from SIGINT')
	logger.critical('Shutting down websocket server.')
	server.close()
	server.wait_closed()
	logger.critical('Server shut down.')
	exit()


if __name__ == '__main__':
	startup()
	signal.signal(signal.SIGINT, sigint)
	loop.run_forever()
