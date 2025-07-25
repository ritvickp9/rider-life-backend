import bcrypt, datetime, secrets

from fastapi import APIRouter
from pydantic import BaseModel, constr
from fastapi.responses import JSONResponse
from db import client, db, sessions_c, users_c
from utils.helper import validate_session, contains_spaces, disallowed_charset
from utils.model import loginResponse, registerResponse, tokenResponse

router = APIRouter()



"""

Login Backend

"""

@router.options("/login")
async def o_login():
	return JSONResponse(content={}, status_code=200)


@router.post("/login")
async def login(request:loginResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)

	username = request.username
	password = request.password	

	if contains_spaces(username) or disallowed_charset(username) or disallowed_charset(password) or contains_spaces(password):
		return JSONResponse(content={'message': 'Empty and/or Invalid Request'}, status_code=401)

	 
	loginCollection = client[db][users_c]
	userData = await loginCollection.find_one({'username':username})

	if userData is None:
		return JSONResponse({'message': 'Invalid username/password'}, status_code=401)	
		
	if bcrypt.checkpw(password.encode('utf-8'), userData['password']):
		
		#Generating a session-token
		token = secrets.token_urlsafe(32)

		sessionCollection = client[db][sessions_c]
		
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


@router.options("/register")
async def o_register():
	return JSONResponse(content={}, status_code=200)

@router.post("/register")
async def register(request: registerResponse = None):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	email = request.email
	password = request.password	

	if contains_spaces(username) or disallowed_charset(username) or disallowed_charset(password) or contains_spaces(password):
		return JSONResponse(content={'message':'Empty and/or Invalid Request!'}, status_code=401)

	loginCollection = client[db][users_c]
	preExistingAcc = await loginCollection.find_one({'username':username})

	if preExistingAcc is not None:
		return JSONResponse({'message': "Username already exists."}, status_code=401)


	hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
	await loginCollection.insert_one({'username':username, 'password':hashedPassword, 'email':email})

	return JSONResponse({"message":"registered"}, status_code=200)

@router.options("/refresh-token")
async def o_refresh():
	return JSONResponse(content={}, status_code=200)

@router.post("/refresh-token")
async def refresh(request:tokenResponse):
	if request is None: return JSONResponse(content={"message":"Empty and/or Invalid Request"}, status_code=401)
	
	username = request.username
	token = request.token

	if not validate_session(username, token):
		return JSONResponse(content={}, status_code=401)
		
	sessionCollection = client[db][sessions_c]
	await sessionCollection.update_one(query_filter, update_operation)
	return JSONResponse({"username":username, "token":token}, status_code=200)