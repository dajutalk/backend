from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from models.events import Event, EventUpdate
from config import settings

async def initialize_database():
    try:
        client= AsyncIOMotorClient(settings.Database_URL)
        await init_beanie(database=client.get_default_database(), document_models=[Event])
    except Exception as e:
        print(f"Error initializing database: {e}")
    
class Database:
    def __init__(self, model:Document) -> None:
        self.model = model

    async def create(self, document: Document) :
        await document.create()
        return
    
    async def get(self) -> list:
        docs = await self.model.find_all().to_list()
        return docs
    

    async def update(self, id: int, body: EventUpdate):
        doc = await self.model.get(id)
        body=body.model_dump()
        body = {"$set":{k: v for k, v in body.items() if v is not None}}
        await doc.update(body)
    
    async def delete(self, id: int):
        doc = await self.model.get(id)
        await doc.delete()