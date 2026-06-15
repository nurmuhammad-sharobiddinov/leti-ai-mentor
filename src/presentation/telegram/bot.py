"""Dispatcher fabrikasi — middleware va router'larni yig'adi."""
from __future__ import annotations

from aiogram import Dispatcher

from ...infrastructure.container import Container
from .middlewares import StudentRegistrationMiddleware
from .routers import (
    build_admin_router,
    build_command_router,
    build_explanation_router,
    build_review_router,
    build_test_router,
)


def build_dispatcher(container: Container) -> Dispatcher:
    dp = Dispatcher()

    # Har bir yangilanishda o'quvchini ro'yxatga olish (message va callback uchun).
    registration = StudentRegistrationMiddleware(container.register_student)
    dp.message.middleware(registration)
    dp.callback_query.middleware(registration)

    # Router'lar tartibi muhim: avval buyruqlar va callback'lar,
    # so'ng umumiy matn handler'i (eng oxirida).
    dp.include_router(build_command_router(container))
    dp.include_router(build_admin_router(container))
    dp.include_router(build_review_router(container))
    dp.include_router(build_test_router(container))
    dp.include_router(build_explanation_router(container))
    return dp
