import datetime, json
from bson import json_util

from fastapi import APIRouter
from pydantic import BaseModel, constr
from fastapi.responses import JSONResponse
from db import client, db, sessions_c, users_c, events_c
from utils.helper import validate_session, contains_spaces, disallowed_charset
from utils.model import Event, addEventResponse, getEventsResponse

router = APIRouter()

"""

Add Events

"""
@router.options("/add")
async def o_add_event():
	return JSONResponse(content={}, status_code=200)

@router.post("/add")
async def add_event(request: addEventResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)
	

	eventName = request.event.eventName
	startDate = request.event.startDate
	endDate = request.event.endDate


	if disallowed_charset(eventName) or startDate>endDate:
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	eventCollection = client[db][events_c]
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

Get Personal Events

"""
@router.options("/get")
async def o_get_events():
	return JSONResponse(content={}, status_code=200)


@router.post("/get")
async def get_events(request: getEventsResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	#Validate the user session
	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)


	eventCollection = client[db][events_c]
	userEvents = await eventCollection.find_one({'username':username})

	if userEvents is None:
		return JSONResponse({"message":"events returned", "events":[]}, status_code=200) 
		
	else:
		for event in userEvents['events']:
			event['startDate'] = event['startDate'].strftime("%Y-%m-%d")
			event['endDate'] = event['endDate'].strftime("%Y-%m-%d")

		return JSONResponse({"message":"bike added", "events":userEvents['events']}, status_code=200)
		
		
"""

Public Events System

"""

@router.options("/public")
async def o_public_events():
	return JSONResponse(content={}, status_code=200)
	
@router.get("/public")
async def public_events():

	# No need for session validation or otherwise checks, since this is just a public list/display of events
	
	eventCollection = client[db][events_c]
	documents = eventCollection.find({})
	eventList = []
	
	async for doc in documents:
		events = doc.get("events", [])
		if isinstance(events, list):
			for event in events:
				event['startDate'] = event['startDate'].strftime("%Y-%m-%d")
				event['endDate'] = event['endDate'].strftime("%Y-%m-%d")
			eventList.extend(events)
	
	return JSONResponse(content={"message":"Events returned", "events": eventList}, status_code=200)

	"""

	if userEvents is None:
		return JSONResponse({"message":"events returned", "events":[]}, status_code=200) 
		
	else:
		for event in userEvents['events']:
			event['startDate'] = event['startDate'].strftime("%Y-%m-%d")
			event['endDate'] = event['endDate'].strftime("%Y-%m-%d")

		return JSONResponse({"message":"bike added", "events":userEvents['events']}, status_code=200)
	"""