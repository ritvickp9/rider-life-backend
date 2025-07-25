import regex,bcrypt, datetime, secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr, Field

from motor.motor_asyncio import AsyncIOMotorClient
#-----------------------------------------------------


app = FastAPI()

connectionURL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(connectionURL)
dbName = 'rider-dev'
userDetailsCollection = 'userDetails'
bikeDetailsCollection = 'bikeDetails'
eventDetailsCollection = 'eventDetails'
sessionDetailsCollection = 'activeSessions'



"""

Helper Functions 

"""





"""

CORS Configuration

"""


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Or set specific origins like ["http://localhost:8081"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
""""

Refresh Session Token

"""
@app.options("/refresh-token")
async def o_refresh():
	return JSONResponse(content={}, status_code=200)

class tokenResponse(BaseModel):
	username: constr(min_length=1)
	token: constr(min_length=1)

@app.post("/refresh-token")
async def refresh(request:tokenResponse):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	
	sessionCollection = client[dbName][sessionDetailsCollection]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return JSONResponse(content={}, status_code=401)
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=45):
			await sessionCollection.delete_one({'username':username})
			return JSONResponse(content={}, status_code=401) 
		else:
			#Generating a new session-token
			token = secrets.token_urlsafe(32)
			query_filter = {"username":username}
			update_operation = {"$set":
				{
					"token":bcrypt.hashpw(token.encode('utf-8'),bcrypt.gensalt()),
					"activation": datetime.datetime.now()
				}
				}
			
			await sessionCollection.update_one(query_filter, update_operation)			

			return JSONResponse({"username":username, "token":token}, status_code=200)


	else:
		return JSONResponse(content={}, status_code=401)
		


"""

Login Backend

"""

@app.options("/login")
async def o_login():
	return JSONResponse(content={}, status_code=200)

class loginResponse(BaseModel):
	username: constr(min_length=1)
	password: constr(min_length=1)

@app.post("/login")
async def login(request: loginResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)

	username = request.username
	password = request.password	

	if contains_spaces(username) or disallowed_charset(username) or disallowed_charset(password) or contains_spaces(password):
		return JSONResponse(content={'message': 'Empty and/or Invalid Request'}, status_code=401)

	 
	loginCollection = client[dbName][userDetailsCollection]
	userData = await loginCollection.find_one({'username':username})

	if userData is None:
		return JSONResponse({'message': 'Invalid username/password'}, status_code=401)	
		
	if bcrypt.checkpw(password.encode('utf-8'), userData['password']):
		
		#Generating a session-token
		token = secrets.token_urlsafe(32)

		sessionCollection = client[dbName][sessionDetailsCollection]
		
		if await sessionCollection.find_one({'username':username}) != None:
			query_filter = {"username":username}
			update_operation = {"$set":
				{
					"token":bcrypt.hashpw(token.encode('utf-8'),bcrypt.gensalt()),
	 				"activation": datetime.datetime.now()
	 			}
				}
			
			await sessionCollection.update_one(query_filter, update_operation)			
		
		else:
			await sessionCollection.insert_one({
				'username':username, 
				'token':bcrypt.hashpw(token.encode('utf-8'),bcrypt.gensalt()),
				'activation':datetime.datetime.now()
				})

		return JSONResponse({"username":username, "token":token}, status_code=200)


	return JSONResponse({"message":"Invalid username/password"}, status_code=401)

"""

Registration Backend

"""


@app.options("/register")
async def o_register():
	return JSONResponse(content={}, status_code=200)


class registerResponse(BaseModel):
	username:constr(min_length=3, max_length=20)
	email:constr(min_length=3)
	password:constr(min_length=8, max_length=64)


@app.post("/register")
async def register(request: registerResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	email = request.email
	password = request.password	

	if contains_spaces(username) or disallowed_charset(username) or disallowed_charset(password) or contains_spaces(password):
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	loginCollection = client[dbName][userDetailsCollection]
	preExistingAcc = await loginCollection.find_one({'username':username})

	if preExistingAcc is not None:
		return JSONResponse({'message': "Username already exists."}, status_code=401)


	hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
	await loginCollection.insert_one({'username':username, 'password':hashedPassword, 'email':email})

	return JSONResponse({"message":"registered"}, status_code=200)

"""

Add bikes

"""
@app.options("/add-bike")
async def o_add_bike():
	return JSONResponse(content={}, status_code=200)

class Bike(BaseModel):
	companyName:constr(min_length=3)
	bikeName:constr(min_length=3)
	year:int = Field(..., ge=1900, le=datetime.datetime.now().year)
	totalDistance: float = Field(...,ge=0)


class addBikeResponse(BaseModel):
	username: constr(min_length=3)
	bike: Bike
	token: constr(min_length=3)



@app.post("/add-bike")
async def add_bike(request: addBikeResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	sessionCollection = client[dbName][sessionDetailsCollection]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return JSONResponse(content={}, status_code=401)
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=45):
			await sessionCollection.delete_one({'username':username})
			return JSONResponse(content={}, status_code=401) 

	else:
		return JSONResponse(content={}, status_code=401)
	


	companyName = request.bike.companyName
	bikeName = request.bike.bikeName
	year = request.bike.year
	totalDistance = request.bike.totalDistance


	if disallowed_charset(companyName) or disallowed_charset(bikeName):
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	bikeCollection = client[dbName][bikeDetailsCollection]
	userBikes = await bikeCollection.find_one({'username':username})

	if userBikes is None:
		await bikeCollection.insert_one({
		'username':username,
		'bikes': {
			bikeName:[companyName, year, totalDistance]
			}
		})
		
		return JSONResponse({"message":"bike added"}, status_code=200) 
		
	else:
		if userBikes['bikes'].get(bikeName) != None: return JSONResponse({"message": "Bike already added/exists."}, status_code=401)
		else:
			query_filter = {"username":username}
			update_operation = {"$set":
				{f"bikes.{bikeName}":[companyName, year, totalDistance]}
				}
			
			await bikeCollection.update_one(query_filter, update_operation)
			return JSONResponse({"message":"bike added"}, status_code=200)
		

"""

Get bikes

"""
@app.options("/get-bikes")
async def o_add_bike():
	return JSONResponse(content={}, status_code=200)


class getBikeResponse(BaseModel):
	username: constr(min_length=3)
	token: constr(min_length=3)



@app.post("/get-bikes")
async def add_bike(request: getBikeResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	sessionCollection = client[dbName][sessionDetailsCollection]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return JSONResponse(content={}, status_code=401)
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=45):
			await sessionCollection.delete_one({'username':username})
			return JSONResponse(content={}, status_code=401) 

	else:
		return JSONResponse(content={}, status_code=401)


	bikeCollection = client[dbName][bikeDetailsCollection]
	userBikes = await bikeCollection.find_one({'username':username})

	if userBikes is None:
		return JSONResponse({"message":"bike added", "bikes":[]}, status_code=200) 
		
	else:
		bikes = []
		for bike in userBikes['bikes']:
			bikes.append(
				{
					'companyName':userBikes['bikes'][bike][0],
					'bikeName':bike,
					'year':userBikes['bikes'][bike][1],
					'totalDistance':userBikes['bikes'][bike][2]
				}
			)
		return JSONResponse({"message":"bike added", "bikes":bikes}, status_code=200)
	

"""

Add Events

"""
@app.options("/add-event")
async def o_add_event():
	return JSONResponse(content={}, status_code=200)

class Event(BaseModel):
	eventName:constr(min_length=3)
	eventDescription:constr(min_length=3)
	eventOrigin:constr(min_length=3)
	eventDestination: constr(min_length=3)
	interestPoints: str
	startDate: datetime.date = Field(..., ge=datetime.date.today())
	endDate: datetime.date = Field(...)
	eventRequirements: str


class addEventResponse(BaseModel):
	username: constr(min_length=3)
	event: Event
	token: constr(min_length=3)



@app.post("/add-event")
async def add_event(request: addEventResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	sessionCollection = client[dbName][sessionDetailsCollection]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return JSONResponse(content={}, status_code=401)
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=45):
			await sessionCollection.delete_one({'username':username})
			return JSONResponse(content={}, status_code=401) 

	else:
		return JSONResponse(content={}, status_code=401)
	

	eventName = request.event.eventName
	startDate = request.event.startDate
	endDate = request.event.endDate


	if disallowed_charset(eventName) or startDate>endDate:
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	eventCollection = client[dbName][eventDetailsCollection]
	userEvents = await eventCollection.find_one({'username':username})

	eventDump = request.event.model_dump()
	eventDump['startDate'] = datetime.datetime.combine(eventDump['startDate'], datetime.time.min)
	eventDump['endDate'] = datetime.datetime.combine(eventDump['endDate'], datetime.time.min)

	if userEvents is None:
		await eventCollection.insert_one({
		'username':username,
		'events': [eventDump]
		})
		
		return JSONResponse({"message":"event added"}, status_code=200) 
		
	else:
		query_filter = {"username":username}
		update_operation = {"$push":
			{"events": eventDump}}
		
		await eventCollection.update_one(query_filter, update_operation)
		return JSONResponse({"message":"event added"}, status_code=200)
		

"""

Get bikes

"""
@app.options("/get-events")
async def o_get_events():
	return JSONResponse(content={}, status_code=200)


class getEventsResponse(BaseModel):
	username: constr(min_length=3)
	token: constr(min_length=3)



@app.post("/get-events")
async def get_events(request: getEventsResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	sessionCollection = client[dbName][sessionDetailsCollection]
	userSession = await sessionCollection.find_one({'username':username})

	if userSession is None: return JSONResponse(content={}, status_code=401)
	if bcrypt.checkpw(token.encode('utf-8'), userSession['token']):
		activationTime = userSession['activation']
		currentTime = datetime.datetime.now()

		if currentTime-activationTime>datetime.timedelta(minutes=45):
			await sessionCollection.delete_one({'username':username})
			return JSONResponse(content={}, status_code=401) 

	else:
		return JSONResponse(content={}, status_code=401)


	eventCollection = client[dbName][eventDetailsCollection]
	userEvents = await eventCollection.find_one({'username':username})

	if userEvents is None:
		return JSONResponse({"message":"events returned", "events":[]}, status_code=200) 
		
	else:
		for event in userEvents['events']:
			event['startDate'] = event['startDate'].strftime("%Y-%m-%d")
			event['endDate'] = event['endDate'].strftime("%Y-%m-%d")

		return JSONResponse({"message":"bike added", "events":userEvents['events']}, status_code=200)