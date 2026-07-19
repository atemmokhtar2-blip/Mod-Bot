"""
Database session middleware.
Injects an AsyncSession into every handler's data dict so handlers
never manage sessions directly.

Future: add request-scoped caching, tenant isolation.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.connection import async_session
from utils.logger import get_logger

log = get_logger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """Opens a session before each update, closes it after."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
