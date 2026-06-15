"""Dependency Injection konteyneri (Composition Root'ning markaziy qismi).

Barcha konkret realizatsiyalar shu yerda port'larga ulanadi. Yuqori qatlamlar
faqat tayyor obyektlarni oladi — qaerdan kelishini bilmaydi.
"""
from __future__ import annotations

from functools import cached_property

from ..application.use_cases import (
    ExplainTopicUseCase,
    GetMyStatsUseCase,
    GetStatisticsUseCase,
    ListReviewsUseCase,
    ProcessDueReviewsUseCase,
    ReexplainTopicUseCase,
    RegisterStudentUseCase,
    StartReviewUseCase,
    StartTestUseCase,
    SubmitAnswerUseCase,
)
from ..domain.services import SpacedRepetitionPolicy
from .clock import SystemClock
from .config import Settings
from .llm import (
    AnthropicClient,
    LlmExplanationService,
    LlmPerformanceAnalyst,
    LlmTestGenerator,
)
from .llm.resilience import AsyncRetrier, Throttler
from .persistence import (
    Database,
    PgConversationRepository,
    PgReviewRepository,
    PgStatisticsRepository,
    PgStudentRepository,
    PgTestSessionRepository,
)


class Container:
    def __init__(self, settings: Settings, db: Database) -> None:
        self._settings = settings
        self._db = db

    @property
    def settings(self) -> Settings:
        return self._settings

    # --- Domen xizmatlari ---

    @cached_property
    def clock(self) -> SystemClock:
        return SystemClock()

    @cached_property
    def review_policy(self) -> SpacedRepetitionPolicy:
        return SpacedRepetitionPolicy()

    # --- Infratuzilma: repozitoriylar ---

    @cached_property
    def students(self) -> PgStudentRepository:
        return PgStudentRepository(self._db)

    @cached_property
    def conversations(self) -> PgConversationRepository:
        return PgConversationRepository(self._db)

    @cached_property
    def sessions(self) -> PgTestSessionRepository:
        return PgTestSessionRepository(self._db)

    @cached_property
    def reviews(self) -> PgReviewRepository:
        return PgReviewRepository(self._db)

    @cached_property
    def statistics(self) -> PgStatisticsRepository:
        return PgStatisticsRepository(self._db)

    # --- Infratuzilma: AI xizmatlari (retry + rate-limit bilan) ---

    @cached_property
    def _anthropic(self) -> AnthropicClient:
        return AnthropicClient(
            api_key=self._settings.anthropic_api_key,
            max_tokens=self._settings.max_tokens,
            retrier=AsyncRetrier(
                max_retries=self._settings.llm_max_retries,
                base_delay=self._settings.llm_retry_base_delay,
            ),
            throttler=Throttler(max_concurrency=self._settings.llm_max_concurrency),
        )

    @cached_property
    def explainer(self) -> LlmExplanationService:
        return LlmExplanationService(
            client=self._anthropic,
            model=self._settings.explainer_model,
            admin_username=self._settings.admin_username,
        )

    @cached_property
    def test_generator(self) -> LlmTestGenerator:
        return LlmTestGenerator(
            client=self._anthropic,
            model=self._settings.test_model,
            question_count=self._settings.questions_per_test,
        )

    @cached_property
    def analyst(self) -> LlmPerformanceAnalyst:
        return LlmPerformanceAnalyst(
            client=self._anthropic,
            model=self._settings.analysis_model,
        )

    # --- Application: use case'lar ---

    @cached_property
    def register_student(self) -> RegisterStudentUseCase:
        return RegisterStudentUseCase(self.students)

    @cached_property
    def explain_topic(self) -> ExplainTopicUseCase:
        return ExplainTopicUseCase(
            students=self.students,
            conversations=self.conversations,
            explainer=self.explainer,
            history_limit=self._settings.history_limit,
        )

    @cached_property
    def reexplain_topic(self) -> ReexplainTopicUseCase:
        return ReexplainTopicUseCase(
            students=self.students,
            conversations=self.conversations,
            explainer=self.explainer,
            history_limit=self._settings.history_limit,
        )

    @cached_property
    def start_test(self) -> StartTestUseCase:
        return StartTestUseCase(
            students=self.students,
            conversations=self.conversations,
            sessions=self.sessions,
            test_generator=self.test_generator,
            history_limit=self._settings.history_limit,
        )

    @cached_property
    def submit_answer(self) -> SubmitAnswerUseCase:
        return SubmitAnswerUseCase(
            students=self.students,
            sessions=self.sessions,
            analyst=self.analyst,
            reviews=self.reviews,
            policy=self.review_policy,
            clock=self.clock,
        )

    @cached_property
    def get_statistics(self) -> GetStatisticsUseCase:
        return GetStatisticsUseCase(self.statistics)

    @cached_property
    def get_my_stats(self) -> GetMyStatsUseCase:
        return GetMyStatsUseCase(self.statistics)

    @cached_property
    def process_due_reviews(self) -> ProcessDueReviewsUseCase:
        return ProcessDueReviewsUseCase(
            reviews=self.reviews,
            clock=self.clock,
            notify_cooldown_hours=self._settings.review_notify_cooldown_hours,
        )

    @cached_property
    def start_review(self) -> StartReviewUseCase:
        return StartReviewUseCase(
            students=self.students,
            conversations=self.conversations,
            reviews=self.reviews,
            explainer=self.explainer,
            policy=self.review_policy,
            clock=self.clock,
            history_limit=self._settings.history_limit,
        )

    @cached_property
    def list_reviews(self) -> ListReviewsUseCase:
        return ListReviewsUseCase(self.reviews)
