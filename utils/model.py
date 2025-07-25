import datetime
from pydantic import BaseModel, constr, Field

class tokenResponse(BaseModel):
	username: constr(min_length=1)
	token: constr(min_length=1)
	
class loginResponse(BaseModel):
	username: constr(min_length=1)
	password: constr(min_length=1)
	
class registerResponse(BaseModel):
	username:constr(min_length=3, max_length=20)
	email:constr(min_length=3)
	password:constr(min_length=8, max_length=64)
	
class Bike(BaseModel):
	companyName:constr(min_length=3)
	bikeName:constr(min_length=3)
	year:int = Field(..., ge=1900, le=datetime.datetime.now().year)
	totalDistance: float = Field(...,ge=0)
	
class addBikeResponse(BaseModel):
	username: constr(min_length=3)
	bike: Bike
	token: constr(min_length=3)
	
class getBikeResponse(BaseModel):
	username: constr(min_length=3)
	token: constr(min_length=3)
	
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
	
class getEventsResponse(BaseModel):
	username: constr(min_length=3)
	token: constr(min_length=3)