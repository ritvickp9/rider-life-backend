from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
load_dotenv()
connectionURL = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(connectionURL)

db = "rider-dev"
users_c = "userDetails"
bikes_c = "bikeDetails"
events_c = "eventDetails"
sessions_c = "activeSessions"
