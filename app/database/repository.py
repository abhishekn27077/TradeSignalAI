from typing import Any, Generic, TypeVar

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Type variable for the SQLAlchemy ORM Model
T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Abstract Base Repository pattern providing generic CRUD operations for SQLAlchemy models.
    """
    
    def __init__(self, model_class: type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session

    async def get_by_id(self, id: Any) -> T | None:
        """Fetch a single record by its primary key."""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id) # type: ignore
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Fetch all records with optional pagination."""
        result = await self.session.execute(
            select(self.model_class).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> T:
        """Create a new record."""
        db_obj = self.model_class(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: Any, obj_in: dict) -> T | None:
        """Update an existing record."""
        await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == id) # type: ignore
            .values(**obj_in)
        )
        await self.session.flush()
        return await self.get_by_id(id)

    async def delete(self, id: Any) -> bool:
        """Delete a record."""
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == id) # type: ignore
        )
        await self.session.flush()
        return result.rowcount > 0
