from typing import Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mongo import Internationalization


class ScreenData(BaseModel):
    name: str


class TagData(BaseModel):
    name: str
    screen: str
    data: Dict[str, str]


app = FastAPI()

# Configuración de CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/screens")
def get_screens():
    connection = Internationalization()
    connection.connect()

    screens_data = connection.get_screens()
    connection.disconnect()
    return screens_data


@app.post("/screens/sync")
def sync_screens():
    connection = Internationalization()
    connection.connect()

    connection.sync_schemas()
    connection.disconnect()


@app.get("/screens/{screen_name}")
def get_screens(screen_name: str):
    connection = Internationalization()
    connection.connect()

    screen_data = connection.get_screens_details(screen_name)
    connection.disconnect()
    return screen_data


@app.post("/tags")
def add_screen(new_tag: TagData):
    print(f"body: {new_tag}")
    connection = Internationalization()
    connection.connect()

    connection.add_new_tag(screen=new_tag.screen, tag=new_tag.name, values=new_tag.data)
    connection.disconnect()


@app.post("/screens")
def add_screen(screen_data: ScreenData):
    print(f"body: {screen_data}")
    connection = Internationalization()
    connection.connect()

    connection.add_new_screen(screen_name=screen_data.name)
    connection.disconnect()


@app.get("/countries")
def get_countries():
    connection = Internationalization()
    connection.connect()

    collection_names = connection.get_collection_names()
    connection.disconnect()
    return collection_names


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
