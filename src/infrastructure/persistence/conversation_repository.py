"""ConversationRepository port'ining Postgres realizatsiyasi.

n8n'dagi memoryPostgresChat node'ining o'rnini bosadi.
"""
from __future__ import annotations

from ...domain.entities import Message
from ...domain.enums import Role
from ...domain.ports import ConversationRepository
from .database import Database


class PgConversationRepository(ConversationRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, chat_id: int, message: Message) -> None:
        await self._db.pool.execute(
            """
            INSERT INTO conversation_messages (chat_id, role, content)
            VALUES ($1, $2, $3)
            """,
            chat_id,
            message.role.value,
            message.content,
        )

    async def history(self, chat_id: int, limit: int) -> list[Message]:
        # Oxirgi `limit` ta xabarni olamiz, so'ng eskidan-yangiga tartiblaymiz.
        rows = await self._db.pool.fetch(
            """
            SELECT role, content, created_at
              FROM conversation_messages
             WHERE chat_id = $1
             ORDER BY id DESC
             LIMIT $2
            """,
            chat_id,
            limit,
        )
        messages = [
            Message(
                role=Role(row["role"]),
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in reversed(rows)
        ]
        return messages

    async def clear(self, chat_id: int) -> None:
        await self._db.pool.execute(
            "DELETE FROM conversation_messages WHERE chat_id = $1", chat_id
        )
