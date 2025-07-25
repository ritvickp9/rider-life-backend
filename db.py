from motor.motor_asyncio import AsyncIOMotorClient

connectionURL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(connectionURL)

db = "rider-dev"
users_c = "userDetails"
bikes_c = "bikeDetails"
events_c = "eventDetails"
sessions_c = "activeSessions"
