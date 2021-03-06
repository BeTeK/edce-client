import sys
if sys.version_info.major < 3:
	print("You need to use Python 3.x, e.g. python3 <filename>")
	exit()

import json	
import hashlib
import time
import datetime
import requests
import math

import edce.config
import edce.globals
import edce.error

testSchema = True

def convertCategoryEDDN(name):
	#Issue #4
	if name == 'Narcotics':
		return 'Legal Drugs'

	if name == 'Slaves':
		return 'Slavery'
		
	return name


def convertCommodityEDDN(name):
	if name == 'Marine Supplies':
		return 'Marine Equipment'

	if name == 'Auto Fabricators':
		return 'Auto-Fabricators'

	if name == 'Hazardous Environment Suits':
		return 'H.E. Suits'

	if name == 'Atmospheric Extractors':
		return 'Atmospheric Processors'

	if name == 'Non Lethal Weapons':
		return 'Non-lethal Weapons'

	if name == 'Terrain Enrichment Systems':
		return 'Land Enrichment Systems'

	if name == 'Agricultural Medicines':
		return 'Agri-Medicines'

	if name == 'Heliostatic Furnaces':
		return 'Microbial Furnaces'

	#Issue #4
	if name == 'Bio Reducing Lichen':
		return 'Bioreducing Lichen'

	if name == 'Basic Narcotics':
		return 'Narcotics'
		
	return name
    
def submitEDDN(data):
	if edce.globals.debug:
		print(">>>>>>>>>>>>>>>> submitEDDN")
	url = edce.config.getString('urls','url_eddn')
	headers = { 'content-type' : 'application/json; charset=utf8' }
	r = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode('utf8'), verify=True)
	if r.status_code == requests.codes.ok:
		return r.text
	else:
		errstr = "Error: EDDN submitEDDN FAIL %s" % r.status_code
		raise edce.error.ErrorEDDN(errstr)	

def getBracket(level):
	if level == 1:
		return "Low"
	elif level == 2:
		return "Med"
	elif level == 3:
		return "High"
	return ""
		
def postMarketData(data):
	if edce.globals.debug:
		print(">>>>>>>>>>>>>>>> postMarketData")

	enable = edce.config.getString('preferences','enable_eddn')
	if enable.lower() != 'yes':
		errstr = "Error: EDDN postMarketData FAIL, EDDN is disabled in edce.ini"
		raise edce.error.ErrorEDDN(errstr)		
		
	username=edce.config.getString('login','username')
	if username == '':
		errstr = "Error: EDDN postMarketData FAIL no username"
		raise edce.error.ErrorEDDN(errstr)
	
	if "docked" in data.commander and data.commander.docked:
		pass
	else:
		errstr = "Error: EDDN postMarketData FAIL pilot must be docked"
		raise edce.error.ErrorEDDN(errstr)
	
	try:
		utf8username = edce.util.convertUTF8(username)
		clientID = hashlib.sha224(utf8username.encode('utf-8')).hexdigest()
		st = datetime.datetime.utcnow().isoformat()
		system = data.lastSystem.name.strip()
		station = data.lastStarport.name.strip()
		schema = 'http://schemas.elite-markets.net/eddn/commodity/1'
		if testSchema:
			schema = schema + '/test'
			
		for commodity in data.lastStarport.commodities:
			if "categoryname" in commodity and commodity.categoryname != "NonMarketable":
				message = {"header": {"softwareVersion": edce.globals.version.strip(), "softwareName": edce.globals.name.strip(), "uploaderID": clientID}, "$schemaRef": schema, "message": {"buyPrice": math.floor(commodity.buyPrice), "timestamp": st, "stationStock": math.floor(commodity.stock), "systemName": system, "stationName": station, "demand":  math.floor(commodity.demand), "sellPrice": math.floor(commodity.sellPrice), "itemName": convertCommodityEDDN(commodity.name.strip()).strip()}}
				if commodity.demandBracket > 0:
					message['message']['demandLevel'] = getBracket(commodity.demandBracket)
				elif commodity.stockBracket > 0:
					message['message']['supplyLevel'] = getBracket(commodity.stockBracket)
				submitEDDN(message)
			else:
				if edce.globals.debug:
					print(">>>>>>>>>>>>>>>> postMarketData skipped " + commodity.name)
	except:
		errstr = "Error: EDDN postMarketData FAIL submit error"
		raise edce.error.ErrorEDDN(errstr)
