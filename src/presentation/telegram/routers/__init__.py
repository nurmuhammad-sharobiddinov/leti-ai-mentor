from .admin import build_admin_router
from .commands import build_command_router
from .explanation import build_explanation_router
from .review import build_review_router
from .test import build_test_router

__all__ = [
    "build_command_router",
    "build_admin_router",
    "build_review_router",
    "build_explanation_router",
    "build_test_router",
]
