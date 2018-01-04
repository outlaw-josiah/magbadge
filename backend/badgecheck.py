#!/bin/env python3
import settings, logging, argparse, requests, asyncio, websockets, json, signal
import textwrap, socket, util
from copy		import deepcopy
from datetime	import datetime
from functools	import partial
from uuid		import UUID
from os			import path, chdir as _chdir, makedirs as _makedirs
# Exceptions
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectTimeout, ConnectionError
from websockets.exceptions import ConnectionClosed


async def getAttndFromMAGAPI(badge):
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
	logger.debug(kwargs)
	try:
		futr_resp = loop.run_in_executor(None, partial(requests.post, **kwargs))
		resp = await futr_resp
		prepped = resp.request
		logger.debug('{}\n{}\n{}\n\n{}'.format(
			'-----------START-----------',
			prepped.method + ' ' + prepped.url,
			'\n'.join('{}: {}'.format(k, v) for k, v in prepped.headers.items()),
			prepped.body,
		))
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
	now = datetime.now()
	filename = "logs/{}{}_scans.csv".format(
		getSetting('logfile_pre'), now.date())
	meal = 'undefined'
	try:
		while sock.open:
			msg = await sock.recv()
			resp = deepcopy(settings.generic_resp)

			# Load JSON and error check it
			try: msgJSON = json.loads(msg)
			except JSONDecodeError as e:
				logger.error(
					'Failed to decode: \n'
					'{}\n{}'.format(
						textwrap.fill(msg, **settings.textwrap_conf),
						textwrap.fill(e.args[0], **settings.textwrap_conf)
					))
				resp['status'] = requests.status_codes.codes.BAD_REQUEST
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
				resp['status'] = requests.status_codes.codes.BAD_REQUEST
				resp['error'] = settings.error.JSON_invalid
				await sock.send(json.dumps(resp))
				continue

			# Done error checking, begin actual code
			if (
				'meal' in msgJSON
				and msgJSON['meal'] in settings.mealtimes
				and msgJSON['meal'] != meal
			):
				logger.info('Updating mealtime')
				meal = msgJSON['meal']
				now = datetime.now()
				filename = "logs/{}{}{}_scans.csv".format(
					getSetting('logfile_pre'),
					now.date(),
					("_" + meal) if meal != 'undefined' else ''
				)
			if 'action' not in msgJSON:
				logger.error('JSON did not include action: {}'.format(msg))
				resp['status'] = requests.status_codes.codes.BAD_REQUEST
				resp['error'] = settings.error.JSON_NOOP
				await sock.send(json.dumps(resp))
				continue
			# TODO: System admin level change
			elif msgJSON['action'] == 'admin':
				pass
			# Badge lookup
			elif msgJSON['action'] == 'query.badge':
				now = datetime.now()
				valid = await getBadge(sock, msgJSON['params'], resp)
				await sock.send(json.dumps(resp))
				if valid:
					util.recordBadge(resp['result'], filename, now)
					util.improve(resp)
				continue
			# TODO: System state lookup
			elif msgJSON['action'] == 'query.state':
				pass
			# Wrap the request into a response and send back
			elif msgJSON['action'] == 'echo':
				logger.warning(
					'Echo request for data on connection {1}:{2}\n'
					'{0}'.format(
						textwrap.fill(msg, **settings.textwrap_conf),
						*sock.remote_address
					))
				resp['status'] = requests.status_codes.codes.OK
				resp['result'] = msgJSON
				await sock.send(json.dumps(resp))
			# Not a valid action, send a response to the client and continue
			else:
				await sock.send("")
	except ConnectionClosed:
		# Healthy error, log in debug mode but otherwise ignore
		logger.debug(
			'Connection {}:{} closed by client'.format(*sock.remote_address))


async def getBadge(sock, badge, resp):
	'''Get badge data and confirm it's a loggable result

	Sends the request to the MAGAPI and parses it for unexpected results
	If anything goes wrong, return FALSE. If the response is good, return
	TRUE'''
	try: data = await getAttndFromMAGAPI(badge)
	except ValueError as e:
		resp['status'] = requests.status_codes.codes.BAD_REQUEST
		resp['error'] = e.args
		return False
	if not data.ok:
		resp['status'] = data.status_code
		resp['error'] = str(data) if data != str() else 'Unknown error'
		return False
	# Load data as a dict
	dataJSON = data.json()
	if 'error' in dataJSON:
		resp['status'] = requests.status_codes.codes.BAD_REQUEST
		resp['error'] = dataJSON['error']
		return False
	if 'error' in dataJSON['result']:
		resp['status'] = requests.status_codes.codes.BAD_REQUEST
		resp['error'] = dataJSON['result']['error']
		return False
	resp['status'] = requests.status_codes.codes.OK
	resp['result'] = simplifyBadge(dataJSON['result'])
	return True


def simplifyBadge(data):
	'''Simplify the response from the MAG API'''
	result = dict(
		badge_num=data['badge_num'], staff=data['staffing'],
		hr_worked=data['worked_hours'], hr_total=data['weighted_hours'],
		ribbons=data['ribbon_labels'], dept_head=data['is_dept_head'],
		badge_t=data['badge_type_label'],
		btext=data['badge_printed_name'], name=data['full_name']
	)
	if data['food_restrictions'] is not None:
		food = data['food_restrictions']
		if len(food['sandwich_pref_labels']) > 1:
			logger.warning('Badge {:>04} had multiple sandwiches: {}'.format(
				badge,
				food['sandwich_pref_labels']
			))
		result['sandwich'] = (
			food['sandwich_pref_labels']
			if food['sandwich_pref_labels'] != str() else
			['None']
		)
		result['restrict'] = [
			food['freeform'] if food['freeform'] != str() else 'None',
			food['standard_labels']
			]
	else:
		result['sandwich'] = ['None']
		result['restrict'] = ['None', []]

	return result


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


def startup():
	'''Do basic setup for the program. This really should only be run once
	but has some basic tests to prevent double-assignment'''
	_chdir(path.dirname(path.abspath(__file__)))
	_makedirs("logs", exist_ok=True)
	global args, logger, loop
	args = parseargs()
	loop = asyncio.get_event_loop()

	# Set up logging
	open(settings.logfile, 'w').close()
	logger = logging.getLogger(__name__)
	rootLogger = logging.getLogger()
	if len(rootLogger.handlers) is 0:
		rootLogger.setLevel(logging.DEBUG)
		conFmt = "[%(levelname)8s] %(name)s: %(message)s"
		ch = logging.StreamHandler()
		ch.setFormatter(logging.Formatter(conFmt))
		rootLogger.addHandler(ch)
		filFmt = "[%(levelname)8s] %(asctime)s %(name)s: %(message)s"
		fh = logging.FileHandler(settings.logfile)
		fh.setFormatter(logging.Formatter(filFmt, "%b-%d %H:%M:%S"))
		rootLogger.addHandler(fh)
		util.setLogLevel(args.verbose, True)
		logger.debug('Logging set up.')
	logger.debug('Args state: {}'.format(args))
	logger.info('Badge check midlayer v{} starting on {} ({})'.format(
		settings.version,
		datetime.now().date(),
		datetime.now().date().strftime("%A")))

	# Set up API key
	try:
		with open(getSetting('apikey')) as f:
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
			socket.gethostbyname_ex(socket.getfqdn())[-1] + ['127.0.0.1'],
			getSetting('l_port')
		))
		for s in server.sockets:
			logger.info('Now listening for connections on {}:{}'.format(
				*s.getsockname()
			))


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
