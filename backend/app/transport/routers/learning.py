"""Learning API router - обучение Domain Parser на основе Comet результатов."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.learning import (
    LearnFromCometRequestDTO,
    LearnFromCometResponseDTO,
    LearningStatisticsDTO,
    LearnedItemDTO
)
from app.usecases import get_parsing_run
import json
import os
import sys

router = APIRouter()
logger = logging.getLogger(__name__)

# Добавляем путь к domain_info_parser в sys.path
domain_parser_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "domain_info_parser")
if domain_parser_path not in sys.path:
    sys.path.insert(0, domain_parser_path)

from learning_engine import LearningEngine

# Глобальный экземпляр learning engine
_learning_engine = None


def get_learning_engine() -> LearningEngine:
    """Получить глобальный экземпляр learning engine."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine


@router.post("/learn-from-comet", response_model=LearnFromCometResponseDTO)
async def learn_from_comet_results(
    request: LearnFromCometRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """
    Обучить Domain Parser на основе успешных результатов Comet.
    
    Логика:
    1. Domain Parser не нашел данные
    2. Comet нашел данные
    3. Система анализирует, где и как Comet нашел данные
    4. Domain Parser запоминает эти паттерны
    """
    run_id = request.runId
    learning_session_id = request.learningSessionId
    
    logger.info(f"=== LEARNING FROM COMET ===")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Learning session: {learning_session_id}")
    logger.info(f"Domains to learn: {len(request.domains)}")
    
    try:
        # Проверяем, что parsing run существует
        parsing_run = await get_parsing_run.execute(db=db, run_id=run_id)
        if not parsing_run:
            raise HTTPException(status_code=404, detail="Parsing run not found")
        
        # Получаем process_log с результатами Domain Parser и Comet
        process_log = getattr(parsing_run, 'process_log', None)
        if not process_log:
            raise HTTPException(status_code=400, detail="No process_log found")
        
        if isinstance(process_log, str):
            try:
                process_log = json.loads(process_log)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid process_log format")
        
        # Получаем результаты Domain Parser
        domain_parser_results = {}
        if "domain_parser" in process_log:
            for parser_run_id, parser_data in process_log["domain_parser"].get("runs", {}).items():
                for result in parser_data.get("results", []):
                    domain_parser_results[result["domain"]] = result
        
        # Получаем результаты Comet
        comet_results = {}
        if "comet" in process_log:
            for comet_run_id, comet_data in process_log["comet"].get("runs", {}).items():
                for result in comet_data.get("results", []):
                    comet_results[result["domain"]] = result
        
        # Обучаемся на каждом домене
        learning_engine = get_learning_engine()
        learned_items = []
        
        for domain in request.domains:
            parser_result = domain_parser_results.get(domain, {})
            comet_result = comet_results.get(domain, {})
            
            if not comet_result:
                logger.warning(f"No Comet result for {domain}, skipping")
                continue
            
            # Проверяем, что Comet нашел что-то, чего не нашел Parser
            comet_inn = comet_result.get("inn")
            comet_email = comet_result.get("email")
            parser_inn = parser_result.get("inn")
            parser_email = parser_result.get("email")
            
            if (comet_inn and not parser_inn) or (comet_email and not parser_email):
                # Есть чему учиться!
                learned = learning_engine.learn_from_comet_success(
                    domain=domain,
                    comet_result=comet_result,
                    parser_result=parser_result,
                    learning_session_id=learning_session_id
                )
                
                if learned["learned_items"]:
                    for item in learned["learned_items"]:
                        learned_items.append(LearnedItemDTO(
                            domain=domain,
                            type=item["type"],
                            value=item["value"],
                            sourceUrls=item["source_urls"],
                            urlPatterns=item["url_patterns"],
                            learning=item["learning"]
                        ))
        
        # Получаем обновленную статистику
        stats = learning_engine.get_statistics()
        
        logger.info(f"✅ Learning completed: {len(learned_items)} items learned")
        
        return LearnFromCometResponseDTO(
            runId=run_id,
            learningSessionId=learning_session_id,
            learnedItems=learned_items,
            statistics=LearningStatisticsDTO(
                totalLearned=stats["total_learned"],
                cometContributions=stats["comet_contributions"],
                successRateBefore=stats["success_rate_before"],
                successRateAfter=stats["success_rate_after"]
            )
        )
        
    except Exception as e:
        logger.error(f"Error in learn_from_comet_results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/statistics", response_model=LearningStatisticsDTO)
async def get_learning_statistics():
    """Получить статистику обучения Domain Parser."""
    try:
        learning_engine = get_learning_engine()
        stats = learning_engine.get_statistics()
        
        return LearningStatisticsDTO(
            totalLearned=stats["total_learned"],
            cometContributions=stats["comet_contributions"],
            successRateBefore=stats["success_rate_before"],
            successRateAfter=stats["success_rate_after"]
        )
    except Exception as e:
        logger.error(f"Error getting learning statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/learned-summary")
async def get_learned_summary(limit: int = 10):
    """Получить краткую сводку выученных паттернов."""
    try:
        learning_engine = get_learning_engine()
        summary = learning_engine.get_learned_summary(limit=limit)
        
        return summary
    except Exception as e:
        logger.error(f"Error getting learned summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
