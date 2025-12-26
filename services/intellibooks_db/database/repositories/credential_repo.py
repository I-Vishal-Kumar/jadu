"""Repository for managing OAuth service credentials."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from asyncpg import Pool
except ImportError:
    Pool = None

logger = logging.getLogger(__name__)


class CredentialRepository:
    """Repository for service credential CRUD operations."""

    def __init__(self, pool: Pool):
        self.pool = pool

    async def save(
        self,
        user_id: str,
        service_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None,
    ) -> bool:
        """Save or update service credentials for a user."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO service_credentials (
                        user_id, service_name, access_token, refresh_token, 
                        expires_at, scope, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    ON CONFLICT (user_id, service_name) DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = COALESCE(EXCLUDED.refresh_token, service_credentials.refresh_token),
                        expires_at = COALESCE(EXCLUDED.expires_at, service_credentials.expires_at),
                        scope = COALESCE(EXCLUDED.scope, service_credentials.scope),
                        updated_at = NOW()
                    """,
                    user_id,
                    service_name,
                    access_token,
                    refresh_token,
                    expires_at,
                    scope,
                )
                logger.info(f"Saved credentials for {user_id}/{service_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to save credential for {user_id}/{service_name}: {e}")
            return False

    async def get(self, user_id: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service credentials for a user."""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, service_name, access_token, refresh_token, 
                           expires_at, scope, created_at, updated_at
                    FROM service_credentials
                    WHERE user_id = $1 AND service_name = $2
                    """,
                    user_id,
                    service_name,
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get credential for {user_id}/{service_name}: {e}")
            return None

    async def delete(self, user_id: str, service_name: str) -> bool:
        """Delete service credentials for a user."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM service_credentials WHERE user_id = $1 AND service_name = $2",
                    user_id,
                    service_name,
                )
                logger.info(f"Deleted credentials for {user_id}/{service_name}")
                return "DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to delete credential for {user_id}/{service_name}: {e}")
            return False
