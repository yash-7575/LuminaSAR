"""
LangGraph Workflow — Hybrid RAG SAR Pipeline

Pipeline:
fetch_data → analyze_patterns → hybrid_rag →
generate_narrative → validate → save_results
"""

from typing import TypedDict, List, Dict, Optional
import pandas as pd
import time
import logging
from datetime import datetime, timezone

from app.services.pattern_detector import PatternDetector
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.audit_logger import AuditLogger
from app.services.validator import NarrativeValidator
from app.config import get_settings

logger = logging.getLogger("luminasar.workflow")
settings = get_settings()


class SARState(TypedDict):
    case_id: str
    customer_id: str
    customer_data: Dict
    transactions: List[Dict]
    patterns: Dict
    typologies: List[str]
    templates: List[str]
    similar_cases: List[str]
    narrative: str
    audit_logs: List[Dict]
    error: Optional[str]
    narrative_id: Optional[str]
    risk_score: float
    audit_steps: int


pattern_detector = PatternDetector()
rag_service = RAGService(persist_directory=settings.chroma_persist_dir)
llm_service = LLMService()
validator = NarrativeValidator()


async def run_sar_workflow(case_id: str, customer_id: str, db) -> Dict:
    logger.info(f"🚀 Starting SAR workflow for case {case_id}")
    start_time = time.time()
    audit_logger = AuditLogger()

    state: SARState = {
        "case_id": case_id,
        "customer_id": customer_id,
        "customer_data": {},
        "transactions": [],
        "patterns": {},
        "typologies": [],
        "templates": [],
        "similar_cases": [],
        "narrative": "",
        "audit_logs": [],
        "error": None,
        "narrative_id": None,
        "risk_score": 0.0,
        "audit_steps": 0,
    }

    logger.info("📥 Step 1: Fetching data...")
    state = _fetch_data(state, db, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    logger.info("🔍 Step 2: Analyzing patterns...")
    state = _analyze_patterns(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    logger.info("📚 Step 3: Hybrid RAG retrieval...")
    state = _retrieve_hybrid_rag(state, audit_logger)

    logger.info("🤖 Step 4: Generating narrative...")
    state = await _generate_narrative(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    logger.info("✅ Step 5: Validating narrative...")
    state = _validate(state, audit_logger)

    logger.info("💾 Step 6: Saving results...")
    state = _save_results(state, db, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    generation_time = int(time.time() - start_time)
    logger.info(f"🏁 Workflow complete in {generation_time}s")

    return {
        "narrative_id": state["narrative_id"],
        "narrative": state["narrative"],
        "risk_score": state["risk_score"],
        "typologies": state["typologies"],
        "audit_steps": len(audit_logger.logs),
    }


def _fetch_data(state: SARState, db, audit_logger: AuditLogger) -> SARState:
    try:
        from app.models.customer import Customer
        from app.models.transaction import Transaction

        customer = (
            db.query(Customer)
            .filter(Customer.customer_id == state["customer_id"])
            .first()
        )

        if not customer:
            state["error"] = "Customer not found"
            return state

        state["customer_data"] = customer.to_dict()

        transactions = (
            db.query(Transaction)
            .filter(Transaction.customer_id == state["customer_id"])
            .all()
        )

        state["transactions"] = [t.to_dict() for t in transactions]

        audit_logger.log_step(
            step_name="fetch_data",
            data_sources={"database": "postgresql"},
            reasoning={"customer_name": customer.name},
            outputs={"transaction_count": len(state["transactions"])},
            confidence=1.0,
        )

    except Exception as e:
        state["error"] = f"Fetch failed: {str(e)}"

    return state


def _analyze_patterns(state: SARState, audit_logger: AuditLogger) -> SARState:
    try:
        df = pd.DataFrame(state["transactions"])
        patterns = pattern_detector.analyze(df)

        state["patterns"] = patterns
        state["typologies"] = patterns["typologies"]
        state["risk_score"] = patterns["risk_score"]

        audit_logger.log_step(
            step_name="analyze_patterns",
            data_sources={"algorithm": "pattern_detector"},
            reasoning={"typologies": patterns["typologies"]},
            outputs={"risk_score": patterns["risk_score"]},
            confidence=0.9,
        )

    except Exception as e:
        state["error"] = f"Pattern analysis failed: {str(e)}"

    return state


def _retrieve_hybrid_rag(state: SARState, audit_logger: AuditLogger) -> SARState:
    try:
        hybrid = rag_service.retrieve_hybrid_context(
            typologies=state["typologies"],
            patterns=state["patterns"],
        )

        state["templates"] = [
            t["template"] if isinstance(t, dict) else str(t)
            for t in hybrid.get("templates", [])
        ]

        state["similar_cases"] = hybrid.get("similar_cases", [])

        audit_logger.log_step(
            step_name="retrieve_hybrid_rag",
            data_sources={"vector_stores": ["chromadb", "faiss"]},
            reasoning={
                "templates_found": len(state["templates"]),
                "similar_cases_found": len(state["similar_cases"]),
            },
            outputs={
                "templates": len(state["templates"]),
                "similar_cases": len(state["similar_cases"]),
            },
            confidence=0.9,
        )

    except Exception as e:
        logger.warning(f"Hybrid RAG failed: {e}")
        state["templates"] = []
        state["similar_cases"] = []

    return state


async def _generate_narrative(state: SARState, audit_logger: AuditLogger) -> SARState:
    try:
        templates_text = "\n\n---\n\n".join(state["templates"])

        similar_cases_text = "\n\n---\n\n".join(
            case[:1200] for case in state["similar_cases"]
        )

        prompt = llm_service.create_sar_prompt(
            customer_data=state["customer_data"],
            transactions=state["transactions"],
            patterns=state["patterns"],
            templates=templates_text,
            typologies=state["typologies"],
            similar_cases=similar_cases_text,
        )

        narrative = await llm_service.generate_narrative(prompt)
        state["narrative"] = narrative

        audit_logger.log_step(
            step_name="generate_narrative",
            data_sources={"model": settings.ollama_model},
            reasoning={"hybrid_rag_used": True},
            outputs={"narrative_length": len(narrative)},
            confidence=0.85,
        )

    except Exception as e:
        state["error"] = f"Narrative generation failed: {str(e)}"

    return state


def _validate(state: SARState, audit_logger: AuditLogger) -> SARState:
    try:
        validation = validator.validate(
            narrative=state["narrative"],
            transactions=state["transactions"],
            customer=state["customer_data"],
        )

        audit_logger.log_step(
            step_name="validate_narrative",
            data_sources={"validator": "rule_based"},
            reasoning={"valid": validation["valid"]},
            outputs={"errors": validation["errors"]},
            confidence=0.95 if validation["valid"] else 0.5,
        )

    except Exception:
        pass

    return state


def _save_results(state: SARState, db, audit_logger: AuditLogger) -> SARState:
    try:
        from app.models.sar_narrative import SARNarrative

        narrative_record = SARNarrative(
            case_id=state["case_id"],
            narrative_text=state["narrative"],
            generation_time_seconds=0,
        )

        db.add(narrative_record)
        db.commit()

        state["narrative_id"] = str(narrative_record.narrative_id)

    except Exception as e:
        db.rollback()
        state["error"] = f"Save failed: {str(e)}"

    return state
