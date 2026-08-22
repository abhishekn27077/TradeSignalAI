import asyncio
from app.database.manager import db_manager

async def init():
    db_manager.connect()
    await db_manager.init_db()
    print("Migration successful")

if __name__ == "__main__":
    asyncio.run(init())
