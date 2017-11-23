# Bind to address (Probably always blank)
addr		= ''
# Bind to port
port		= 28000
logfile		= "staging.csv"

# API access creds
crtfile		= "client.crt"
keyfile		= "client.key"

# Hours from GMT that log files should use (Hardcoded for now)
tz_offset   = -5

# MAGFest API options/metadata
magapiopts	= dict(
	cert	= (crtfile, keyfile),
	headers = { "Content-Type": "application/json"},
	json	= { "jsonrpc":  "2.0",
				"method":   "barcode.lookup_attendee_from_barcode",
				"id":		"magbadgeserver-staffsuite"},
	timeout = 3,
	url = "https://onsite.uber.magfest.org:4444/jsonrpc/"
)

