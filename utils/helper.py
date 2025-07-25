import regex, bcrypt, datetime, secrets
from db import client, db, sessions_c

TOKEN_TIMEOUT = 30

#Requests won't be tolerated if they contain any space at all.
def contains_spaces(obj):
	if regex.fullmatch(r'\S+', obj) is None: return True
	return False

def disallowed_charset(obj):
	#Currently acceptable charset: ASCII [20-126]
	if regex.fullmatch(r'[\x20-\x7e]+',obj) is None: return True
	return False
	
async def validate_session(username, token):
	sessionCollection = client[db][sessions_c]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return False
	
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=TOKEN_TIMEOUT):
			await sessionCollection.delete_one({'username':username})
			return False
	else:
		return False
	
	return True