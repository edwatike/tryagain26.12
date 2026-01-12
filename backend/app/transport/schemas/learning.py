"""Learning schemas - DTO для обучения Domain Parser."""

from typing import List, Optional
from pydantic import BaseModel, Field


class LearnedItemDTO(BaseModel):
    """Информация о выученном элементе."""
    domain: str = Field(..., description="Домен, на котором обучились")
    type: str = Field(..., description="Тип данных: 'inn' или 'email'")
    value: str = Field(..., description="Найденное значение (ИНН или Email)")
    sourceUrls: List[str] = Field(default_factory=list, description="URL источников, где найдены данные")
    urlPatterns: List[str] = Field(default_factory=list, description="Выученные URL паттерны")
    learning: str = Field(..., description="Описание того, чему научились")


class LearnFromCometRequestDTO(BaseModel):
    """Запрос на обучение из результатов Comet."""
    runId: str = Field(..., description="ID parsing run")
    learningSessionId: Optional[str] = Field(None, description="ID сессии обучения")
    domains: List[str] = Field(..., description="Домены для обучения")


class LearningStatisticsDTO(BaseModel):
    """Статистика обучения."""
    totalLearned: int = Field(0, description="Всего выучено паттернов")
    cometContributions: int = Field(0, description="Количество обучений от Comet")
    successRateBefore: float = Field(0.0, description="Процент успеха до обучения")
    successRateAfter: float = Field(0.0, description="Процент успеха после обучения")


class LearnFromCometResponseDTO(BaseModel):
    """Ответ на запрос обучения."""
    runId: str = Field(..., description="ID parsing run")
    learningSessionId: Optional[str] = Field(None, description="ID сессии обучения")
    learnedItems: List[LearnedItemDTO] = Field(default_factory=list, description="Выученные элементы")
    statistics: LearningStatisticsDTO = Field(..., description="Статистика обучения")
