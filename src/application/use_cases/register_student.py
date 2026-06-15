"""O'quvchini ro'yxatga olish/yangilash use case'i.

n8n'dagi "Insert or update rows" node'ining toza ekvivalenti.
"""
from __future__ import annotations

from ...domain.entities import Student
from ...domain.ports import StudentRepository


class RegisterStudentUseCase:
    def __init__(self, students: StudentRepository) -> None:
        self._students = students

    async def execute(self, chat_id: int, full_name: str) -> Student:
        existing = await self._students.get(chat_id)
        if existing is not None:
            existing.full_name = full_name or existing.full_name
            await self._students.save(existing)
            return existing

        student = Student(chat_id=chat_id, full_name=full_name or "Anonim")
        return await self._students.upsert(student)
