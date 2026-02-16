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
from app.services.graph_service import KnowledgeGraphService
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
    graph_evidence: Optional[str]
    graph_insight: Optional[str]
    jurisdiction: str
    duration: int


# Initialize services (singletons)
pattern_detector = PatternDetector()
rag_service = RAGService(persist_directory=settings.chroma_persist_dir)
llm_service = LLMService()
validator = NarrativeValidator()
graph_service = KnowledgeGraphService()


async def run_sar_workflow(
    case_id: str, customer_id: str, db, jurisdiction: Optional[str] = None
) -> Dict:
    """Run the complete SAR generation workflow.

    Args:
        case_id: UUID of the SAR case
        customer_id: UUID of the customer
        db: SQLAlchemy database session
        jurisdiction: Optional jurisdiction override (falls back to settings)

    Returns:
        Dictionary with narrative_id, narrative text, risk_score, typologies, audit_steps
    """
    effective_jurisdiction = jurisdiction or settings.jurisdiction
    logger.info(
        f"🚀 Starting SAR workflow for case {case_id} (jurisdiction={effective_jurisdiction})"
    )
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
        "graph_evidence": "",
        "graph_insight": "",
        "jurisdiction": effective_jurisdiction,
        "duration": 0,
    }

    # === STEP 1: Fetch Data ===
    logger.info(f"[{case_id}] 📥 Step 1: Fetching data...")
    state = _fetch_data(state, db, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 2: Analyze Patterns ===
    logger.info(f"[{case_id}] 🔍 Step 2: Analyzing patterns...")
    state = _analyze_patterns(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 3: Retrieve Templates ===
    logger.info(f"[{case_id}] 📚 Step 3: Retrieving templates...")
    state = _retrieve_templates(state, audit_logger)

    # === STEP 3.5: Enrich with Knowledge Graph ===
    logger.info(f"[{case_id}] 🕸️ Step 3.5: Enriching with Knowledge Graph...")
    state = _enrich_with_knowledge_graph(state, audit_logger)

    # === STEP 4: Generate Narrative ===
    logger.info(f"[{case_id}] 🤖 Step 4: Generating narrative...")
    state = await _generate_narrative(state, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    # === STEP 5: Validate ===
    logger.info(f"[{case_id}] ✅ Step 5: Validating narrative...")
    state = _validate(state, audit_logger)

    # Calculate actual generation time before saving
    state["duration"] = int(time.time() - start_time)

    # === STEP 6: Save Results ===
    logger.info(f"[{case_id}] 💾 Step 6: Saving results (duration={state['duration']}s)...")
    state = _save_results(state, db, audit_logger)
    if state["error"]:
        raise Exception(state["error"])

    logger.info(f"[{case_id}] 🏁 Workflow complete in {state['duration']}s")

    return {
        "narrative_id": state["narrative_id"],
        "narrative": state["narrative"],
        "risk_score": state["risk_score"],
        "typologies": state["typologies"],
        "audit_steps": len(audit_logger.logs),
        "generation_time_seconds": state["duration"],
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


def _enrich_with_knowledge_graph(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 3.5: Enrich detected typologies with Knowledge Graph evidence."""
    try:
        jurisdiction = state["jurisdiction"]
        graph_data = graph_service.get_typology_context(
            state["typologies"], jurisdiction=jurisdiction
        )

        state["graph_evidence"] = graph_data["evidence_text"]
        state["graph_insight"] = graph_data["insight_text"]

        # Network-based relationship analysis using transaction data
        account_num = state["customer_data"].get("account_number", "unknown")
        relationship_result = graph_service.analyze_relationships(
            account_num, transactions=state["transactions"]
        )
        state["graph_insight"] += f" {relationship_result['relationship_summary']}"

        audit_logger.log_step(
            step_name="enrich_with_knowledge_graph",
            data_sources={
                "typologies": state["typologies"],
                "jurisdiction": jurisdiction,
                "graph_db": "Neo4j (simulated with networkx)",
                "transaction_count": len(state["transactions"]),
            },
            reasoning={
                "action": "Mapped flat typologies to formal jurisdictional advisories and performed network graph analysis",
                "advisories_matched": len(graph_data.get("advisories", [])),
                "centrality_score": relationship_result.get("centrality_score", 0),
                "cycles_detected": relationship_result.get("cycles_detected", 0),
                "risk_amplification": relationship_result.get("risk_amplification_factor", 1.0),
                "confidence": graph_data.get("confidence_score", 0.3),
            },
            outputs={
                "graph_mapped": len(state["typologies"]) > 0,
                "risk_amplification_factor": relationship_result.get("risk_amplification_factor", 1.0),
            },
            confidence=graph_data.get("confidence_score", 0.3),
        )

    except Exception as e:
        logger.warning(f"Graph enrichment failed: {e}")
        state["graph_evidence"] = "Graph service unavailable."
        state["graph_insight"] = "Defaulting to flat vector analysis."

    return state


async def _generate_narrative(state: SARState, audit_logger: AuditLogger) -> SARState:
    """Step 4: Generate SAR narrative with LLM."""
    try:
        prompt = await llm_service.create_sar_prompt(
            customer_data=state["customer_data"],
            transactions=state["transactions"],
            patterns=state["patterns"],
            templates=state["templates"],
            typologies=state["typologies"],
            jurisdiction=state["jurisdiction"],
            graph_evidence=state.get("graph_evidence", "No graph relationships detected."),
            graph_insight=state.get("graph_insight", "Flat vector search used for typologies."),
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
                "jurisdiction": state["jurisdiction"],
            },
            reasoning={
                "generation_method": "grounded_prompt_with_rag_and_knowledge_graph",
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
            jurisdiction=state["jurisdiction"],
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
            generation_time_seconds=state["duration"],
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
