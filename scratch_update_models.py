import asyncio
from app.database.manager import db_manager
from app.database.models.forecast import ForecastModelMetadata
from sqlalchemy import select, delete
from app.forecast_engine.registry.manager import model_registry

async def update_db():
    db_manager.connect()
    await db_manager.init_db()
    
    session_factory = db_manager.get_session()
    async with session_factory() as session:
        # Delete old LSTM-Standard
        await session.execute(delete(ForecastModelMetadata).where(ForecastModelMetadata.name == "LSTM-Standard"))
        await session.commit()
        
    await model_registry.ensure_default_providers()
    print("Database updated!")

if __name__ == "__main__":
    asyncio.run(update_db())
