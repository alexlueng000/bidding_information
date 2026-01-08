from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import bidding

app = FastAPI()

allow_origins = [
    "http://localhost:3000",
    "https://b49d-120-229-55-240.ngrok-free.app",
    "http://43.142.103.194:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

# Include router with both prefixes for compatibility
app.include_router(bidding.router, prefix="/api/v1")
app.include_router(bidding.router, prefix="/v1")
