"""Database connection management for the Audio Transcription Tool."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.database.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None

    def _get_async_url(self) -> str:
        """Convert sync URL to async URL for SQLite."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return url

    @property
    def async_engine(self):
        """Get or create async engine."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self._get_async_url(),
                echo=False,
                future=True,
            )
        return self._async_engine

    @property
    def sync_engine(self):
        """Get or create sync engine."""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self.database_url,
                echo=False,
                future=True,
            )
            # Enable foreign keys for SQLite
            if "sqlite" in self.database_url:

                @event.listens_for(self._sync_engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

        return self._sync_engine

    @property
    def async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_factory

    @property
    def sync_session_factory(self) -> sessionmaker[Session]:
        """Get or create sync session factory."""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False,
            )
        return self._sync_session_factory

    async def init_database(self) -> None:
        """Initialize the database schema."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def init_database_sync(self) -> None:
        """Initialize the database schema synchronously."""
        Base.metadata.create_all(bind=self.sync_engine)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_sync_session(self) -> Session:
        """Get a sync database session."""
        return self.sync_session_factory()

    async def close(self) -> None:
        """Close all database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_db() -> None:
    """Initialize the database."""
    settings.ensure_directories()
    db_manager = get_db_manager()
    await db_manager.init_database()
