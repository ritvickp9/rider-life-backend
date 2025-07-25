from fastapi import APIRouter
from pydantic import BaseModel, constr
from fastapi.responses import JSONResponse
from db import client, db, sessions_c, users_c, bikes_c
from utils.helper import validate_session, contains_spaces, disallowed_charset
from utils.model import addBikeResponse, Bike, getBikeResponse

router = APIRouter()

"""

Add bikes

"""
@router.options("/add")
async def o_add_bike():
	return JSONResponse(content={}, status_code=200)

@router.post("/add")
async def add_bike(request: addBikeResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)

	companyName = request.bike.companyName
	bikeName = request.bike.bikeName
	year = request.bike.year
	totalDistance = request.bike.totalDistance


	if disallowed_charset(companyName) or disallowed_charset(bikeName):
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	bikeCollection = client[db][bikes_c]
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
@router.options("/get")
async def o_add_bike():
	return JSONResponse(content={}, status_code=200)

@router.post("/get")
async def add_bike(request: getBikeResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)

	bikeCollection = client[db][bikes_c]
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

Edit bikes

"""
@router.options("/update")
async def o_updatebike():
	return JSONResponse(content={}, status_code=200)

@router.post("/update")	
async def update_bike(request: addBikeResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)

	companyName = request.bike.companyName
	bikeName = request.bike.bikeName
	year = request.bike.year
	totalDistance = request.bike.totalDistance


	if disallowed_charset(companyName) or disallowed_charset(bikeName):
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	bikeCollection = client[db][bikes_c]
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
		