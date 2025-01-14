from fastapi import FastAPI
from app.api.endpoints import bidding

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

app.include_router(bidding.router, prefix="/api/v1")
