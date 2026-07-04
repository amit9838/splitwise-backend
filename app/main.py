from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import users, categories, transactions

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(categories.router)
app.include_router(transactions.router)


@app.get("/")
async def health():
    return {"message": "Healthy"}