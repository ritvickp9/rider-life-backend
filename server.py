from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000", "https://rider-life-nextjs.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

from routes import users, bikes, events

app.include_router(users.router, prefix="/user")
app.include_router(bikes.router, prefix="/bikes")
app.include_router(events.router, prefix="/events")