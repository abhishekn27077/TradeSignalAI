import asyncio
import logging
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.manager import db_manager
from app.database.models.user import UserModel, RoleEnum
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def seed_admin():
    db_manager.connect()
    try:
        from app.database.core import Base
        async with db_manager._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all) # Ensure tables exist
        
        Session = db_manager.get_session()
        async with Session() as session:
            from sqlalchemy import select
            result = await session.execute(select(UserModel).where(UserModel.email == "admin@tradesignal.ai"))
            existing_admin = result.scalars().first()
            
            if existing_admin:
                logger.info("Admin user already exists. Skipping seed.")
            else:
                admin_user = UserModel(
                    email="admin@tradesignal.ai",
                    hashed_password=get_password_hash("Admin123!"),
                    full_name="System Administrator",
                    role=RoleEnum.ADMIN.value,
                    is_active=True,
                    is_superuser=True
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Successfully seeded admin user (admin@tradesignal.ai / Admin123!).")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_admin())
