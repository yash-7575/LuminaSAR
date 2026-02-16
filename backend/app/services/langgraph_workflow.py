"""LangGraph Workflow — Orchestrates the 6-step SAR generation pipeline.

Pipeline: fetch_data → analyze_patterns → retrieve_templates →
          generate_narrative → validate → save_results

Each step is logged to the audit trail with hash-chain integrity.
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
    """State object passed through the workflow pipeline."""

    case_id: str
    customer_id: str
    customer_data: Dict
    transactions: List[Dict]
    patterns: Dict
    typologies: List[str]
    templates: List[str]
    narrative: str
    audit_logs: List[Dict]
    error: Optional[str]
    narrative_id: Optional[str]
    risk_score: float
    audit_steps: int


# Initialize services (singletons)
pattern_detector = PatternDetector()
rag_service = RAGService(persist_directory=settings.chroma_persist_dir)
llm_service = LLMService()
validator = NarrativeValidator()


async def run_sar_workflow(case_id: str, customer_id: str, db) -> Dict:
    """Run the complete SAR generation workflow.

    Args:
        case_id: UUID of the SAR case
        customer_id: UUID of the customer
        db: SQLAlchemy database session

    Returns:
        Dictionary with narrative_id, narrative text, risk_score, typologies, audit_steps
    """
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
        "narrative": "",
        "audit_logs": [],
        "error": None,
        "narrative_id": None,
        "risk_score": 0.0,
        "audit_steps": 0,
    }

    # === STEP 1: Fetch Data ===
    logger.info("📥 Step 1: Fetching data...")
    state = _fetch_data(state, db, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 2: Analyze Patterns ===
    logger.info("🔍 Step 2: Analyzing patterns...")
    state = _analyze_patterns(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 3: Retrieve Templates ===
    logger.info("📚 Step 3: Retrieving templates...")
    state = _retrieve_templates(state, audit_logger)

    # === STEP 4: Generate Narrative ===
    logger.info("🤖 Step 4: Generating narrative...")
    state = await _generate_narrative(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 5: Validate ===
    logger.info("✅ Step 5: Validating narrative...")
    state = _validate(state, audit_logger)

    # === STEP 6: Save Results ===
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
    """Step 1: Fetch customer and transaction data from database."""
    try:
        from app.models.customer import Customer
        from app.models.transaction import Transaction

        customer = (
            db.query(Customer)
            .filter(Customer.customer_id == state["customer_id"])
            .first()
        )

        if not customer:
            state["error"] = f"Customer {state['customer_id']} not found"
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
            data_sources={
                "customer_id": state["customer_id"],
                "database": "supabase_postgresql",
            },
            reasoning={
                "action": "Fetched customer KYC data and transaction history",
                "customer_name": customer.name,
            },
            outputs={
                "transaction_count": len(state["transactions"]),
                "customer_found": True,
            },
            confidence=1.0,
        )

    except Exception as e:
        state["error"] = f"Data fetch failed: {str(e)}"
        logger.error(f"❌ {state['error']}")

    return state


def _analyze_patterns(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 2: Detect suspicious patterns using ML."""
    try:
        df = pd.DataFrame(state["transactions"])
        patterns = pattern_detector.analyze(df)

        state["patterns"] = patterns
        state["typologies"] = patterns["typologies"]
        state["risk_score"] = patterns["risk_score"]

        audit_logger.log_step(
            step_name="analyze_patterns",
            data_sources={
                "transaction_ids": [
                    t["transaction_id"][:8] for t in state["transactions"][:10]
                ],
                "total_transactions": len(state["transactions"]),
            },
            reasoning={
                "velocity": patterns["velocity"],
                "structuring": patterns["structuring"],
                "network_summary": {
                    "unique_sources": patterns["network"]["unique_sources"],
                    "unique_destinations": patterns["network"]["unique_destinations"],
                },
                "detection_algorithms": [
                    "velocity_analysis",
                    "volume_analysis",
                    "structuring_detection",
                    "network_graph_analysis",
                    "typology_matching",
                ],
            },
            outputs={
                "typologies": patterns["typologies"],
                "risk_score": patterns["risk_score"],
            },
            confidence=0.92,
        )

    except Exception as e:
        state["error"] = f"Pattern analysis failed: {str(e)}"
        logger.error(f"❌ {state['error']}")

    return state


def _retrieve_templates(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 3: Retrieve relevant SAR templates via RAG."""
    try:
        retrieved = rag_service.retrieve_templates(state["typologies"], top_k=3)
        state["templates"] = [r["template"] for r in retrieved]

        audit_logger.log_step(
            step_name="retrieve_templates",
            data_sources={
                "typologies": state["typologies"],
                "vector_store": "chromadb",
                "embedding_model": "all-MiniLM-L6-v2",
            },
            reasoning={
                "query": f"SAR templates for {', '.join(state['typologies'])}",
                "templates_found": len(state["templates"]),
                "sources": [r.get("source", "unknown") for r in retrieved],
            },
            outputs={
                "templates_retrieved": len(state["templates"]),
            },
            confidence=0.88,
        )

    except Exception as e:
        logger.warning(f"Template retrieval failed: {e}, using defaults")
        state["templates"] = []

    return state


async def _generate_narrative(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 4: Generate SAR narrative with LLM."""
    try:
        prompt = llm_service.create_sar_prompt(
            customer_data=state["customer_data"],
            transactions=state["transactions"],
            patterns=state["patterns"],
            templates=state["templates"],
            typologies=state["typologies"],
        )

        narrative = await llm_service.generate_narrative(prompt)
        state["narrative"] = narrative

        audit_logger.log_step(
            step_name="generate_narrative",
            data_sources={
                "llm_model": settings.ollama_model,
                "prompt_length_chars": len(prompt),
                "templates_used": len(state["templates"]),
                "typologies": state["typologies"],
            },
            reasoning={
                "generation_method": "grounded_prompt_with_rag",
                "temperature": 0.3,
                "grounding_strategy": "All data embedded in prompt, LLM instructed to use only provided data",
            },
            outputs={
                "narrative_length_chars": len(narrative),
                "narrative_word_count": len(narrative.split()),
            },
            confidence=0.85,
        )

    except Exception as e:
        state["error"] = f"Narrative generation failed: {str(e)}"
        logger.error(f"❌ {state['error']}")

    return state


def _validate(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 5: Validate narrative for hallucinations."""
    try:
        validation = validator.validate(
            narrative=state["narrative"],
            transactions=state["transactions"],
            customer=state["customer_data"],
        )

        llm_validation = llm_service.validate_narrative(
            narrative=state["narrative"],
            source_data={"transactions": state["transactions"]},
        )

        audit_logger.log_step(
            step_name="validate_narrative",
            data_sources={
                "narrative_length": len(state["narrative"]),
                "validation_checks": ["structure", "hallucination", "completeness"],
            },
            reasoning={
                "structure_valid": validation["valid"],
                "word_count": validation["word_count"],
                "sections_found": validation["sections_found"],
                "warnings": validation["warnings"] + llm_validation.get("warnings", []),
                "errors": validation["errors"] + llm_validation.get("errors", []),
            },
            outputs={
                "valid": validation["valid"],
            },
            confidence=0.95 if validation["valid"] else 0.5,
        )

        if not validation["valid"]:
            logger.warning(f"⚠️ Validation issues: {validation['errors']}")

    except Exception as e:
        logger.warning(f"Validation step failed: {e}")

    return state


def _save_results(state: SARState, db, audit_logger: AuditLogger) -> SARState:
    """Step 6: Save narrative and audit trail to database."""
    try:
        from app.models.sar_narrative import SARNarrative
        from app.models.sar_case import SARCase
        from app.models.audit_trail import AuditTrail as AuditTrailModel

        # Create sentence attribution
        attribution = audit_logger.create_sentence_attribution(
            state["narrative"], state["transactions"]
        )

        # Log the save step with attribution
        audit_logger.log_step(
            step_name="save_results",
            data_sources={
                "sentence_attribution": attribution,
            },
            reasoning={
                "action": "Saving narrative and audit trail to database",
                "chain_valid": audit_logger.verify_chain(),
            },
            outputs={
                "total_audit_steps": len(audit_logger.logs),
                "sentences_with_data_refs": sum(
                    1 for s in attribution.values() if s.get("has_data_reference")
                ),
            },
            confidence=1.0,
        )

        # Save narrative
        narrative_record = SARNarrative(
            case_id=state["case_id"],
            narrative_text=state["narrative"],
            generation_time_seconds=0,
        )
        db.add(narrative_record)
        db.flush()

        state["narrative_id"] = str(narrative_record.narrative_id)

        # Update case with risk score and typologies
        case = db.query(SARCase).filter(SARCase.case_id == state["case_id"]).first()
        if case:
            case.risk_score = state["risk_score"]
            case.typologies = state["typologies"]
            case.status = "generated"

        # Save audit logs
        for log in audit_logger.logs:
            audit_record = AuditTrailModel(
                narrative_id=narrative_record.narrative_id,
                step_name=log["step_name"],
                data_sources=log["data_sources"],
                reasoning=log["reasoning"],
                confidence_scores=log["confidence_scores"],
                previous_hash=log["previous_hash"],
                current_hash=log["current_hash"],
            )
            db.add(audit_record)

        db.commit()
        logger.info(
            f"💾 Saved narrative {state['narrative_id']} with {len(audit_logger.logs)} audit entries"
        )

    except Exception as e:
        db.rollback()
        state["error"] = f"Database save failed: {str(e)}"
        logger.error(f"❌ {state['error']}")

    return state
