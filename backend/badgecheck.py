import settings, logging
from uuid import UUID


def startup():
	# Set up logging
	logging.basicConfig(format = "[%(levelname)8s] %(name)s: %(message)s")
	logger = logging.getLogger(__name__);
	logger.debug('Logging set up.')

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
