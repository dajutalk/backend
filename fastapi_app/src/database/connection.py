from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from ..models.stock import Stock
from config import settings

async def initialize_database():
    try:
        client= AsyncIOMotorClient(settings.Database_URL)
        await init_beanie(database=client.get_default_database(), document_models=[Stock])
    except Exception as e:
        print(f"Error initializing database: {e}")
    
class Database:
    def __init__(self, model:Document) -> None:
        self.model = model

    async def get(self) -> list:
        docs = await self.model.find_all().to_list()
        return docs
    
