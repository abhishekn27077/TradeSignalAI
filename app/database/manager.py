import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.exceptions import DatabaseException
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    def __init__(self):
        self._engine = None
        self._session_factory = None

    def connect(self):
        db_url = settings.DATABASE_URL
        if not db_url:
            logger.info("DATABASE_URL not configured, using canonical SQLite database tradesignal.db")
            db_url = "sqlite+aiosqlite:///./tradesignal.db"

        def _create_engine(url):
            if url.startswith("sqlite"):
                return create_async_engine(
                    url,
                    echo=False,  # Disabled to prevent console spam
                    future=True,
                    connect_args={"check_same_thread": False, "timeout": 30}
                )
            else:
                return create_async_engine(
                    url,
                    echo=False,  # Disabled to prevent console spam
                    future=True,
                    pool_pre_ping=True,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                )

        try:
            self._engine = _create_engine(db_url)
            self._session_factory = async_sessionmaker(
                bind=self._engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Canonical Database connection pool initialized.")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}, falling back to SQLite tradesignal.db")
            try:
                db_url = "sqlite+aiosqlite:///./tradesignal.db"
                self._engine = _create_engine(db_url)
                self._session_factory = async_sessionmaker(
                    bind=self._engine, class_=AsyncSession, expire_on_commit=False
                )
                logger.info("Canonical Database connection pool initialized.")
            except Exception as e2:
                logger.error(f"Database creation failed: {e2}")
                self._engine = None
                self._session_factory = None

    async def init_db(self):
        if self._engine:
            from app.database.core import Base
            import app.database.models  # noqa: registers all tables with Base

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Canonical database tables initialized and verified.")

    async def disconnect(self):
        if self._engine:
            try:
                await self._engine.dispose()
                logger.info("Database connection pool disposed.")
            except Exception as e:
                logger.debug(f"Database dispose error: {e}")

    def get_session(self) -> async_sessionmaker[AsyncSession] | None:
        return self._session_factory


db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if db_manager._session_factory is None:
        raise DatabaseException("Database not configured")

    async with db_manager._session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()