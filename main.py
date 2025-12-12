from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.models.profile import BaseProfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

items = {}


@app.get("/")
def home():
    return {"Grettings": "Salut tout le monde!"}


@app.post("/profiling/")
def profiling(data: BaseProfile):
    return data
