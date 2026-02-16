"""RAG Service — Retrieval-Augmented Generation using ChromaDB.

Manages a vector store of SAR templates and regulatory guidelines
for context-aware narrative generation.
"""

from typing import List, Dict
import logging
import os

logger = logging.getLogger("luminasar.rag_service")

try:
    import chromadb

    HAS_CHROMADB = True
except (ImportError, Exception) as e:
    HAS_CHROMADB = False
    logger.warning(f"chromadb unavailable ({e}), RAG will use fallback templates")


class RAGService:
    """Manages ChromaDB vector store for SAR template retrieval."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _get_client(self):
        """Lazy-initialize ChromaDB client."""
        if not HAS_CHROMADB:
            return None
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.persist_directory)
        return self._client

    def _get_collection(self):
        """Lazy-initialize collection."""
        if not HAS_CHROMADB:
            return None
        if self._collection is None:
            client = self._get_client()
            if client is None:
                return None
            self._collection = client.get_or_create_collection(
                name="sar_templates",
                metadata={"description": "SAR templates and regulatory guidelines"},
            )
        return self._collection

    def _get_embedding_fn(self):
        """Lazy-initialize sentence transformer."""
        if self._embedding_fn is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedding_fn = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ Loaded sentence-transformers (all-MiniLM-L6-v2)")
            except ImportError:
                logger.warning(
                    "⚠️ sentence-transformers not installed, using basic embeddings"
                )
                self._embedding_fn = None
        return self._embedding_fn

    def load_templates(self, templates_dir: str) -> int:
        """Load SAR templates from text files into ChromaDB.

        Args:
            templates_dir: Path to directory containing .txt template files

        Returns:
            Number of templates loaded
        """
        from pathlib import Path

        templates_path = Path(templates_dir)
        if not templates_path.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return 0

        documents = []
        metadatas = []
        ids = []

        for i, file_path in enumerate(templates_path.glob("*.txt")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        continue

                    documents.append(content)

                    # Extract typology from filename
                    parts = file_path.stem.split("_")
                    typology = parts[1] if len(parts) > 1 else "general"

                    metadatas.append(
                        {
                            "typology": typology,
                            "source": file_path.name,
                        }
                    )
                    ids.append(f"template_{i}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")

        if documents:
            collection = self._get_collection()
            embedding_model = self._get_embedding_fn()

            if embedding_model:
                embeddings = embedding_model.encode(documents).tolist()
                collection.upsert(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
            else:
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )

            logger.info(f"✅ Loaded {len(documents)} templates into ChromaDB")

        return len(documents)

    def retrieve_templates(self, typologies: List[str], top_k: int = 3) -> List[Dict]:
        """Retrieve relevant SAR templates based on detected typologies.

        Args:
            typologies: List of detected money laundering typologies
            top_k: Number of templates to retrieve

        Returns:
            List of dictionaries containing template text and metadata
        """
        try:
            collection = self._get_collection()

            if collection is None or collection.count() == 0:
                logger.warning(
                    "ChromaDB collection is empty, returning default template"
                )
                return [self._get_default_template()]

            query_text = f"SAR narrative for {', '.join(typologies)} money laundering suspicious activity patterns"
            embedding_model = self._get_embedding_fn()

            if embedding_model:
                query_embedding = embedding_model.encode([query_text]).tolist()
                results = collection.query(
                    query_embeddings=query_embedding,
                    n_results=min(top_k, collection.count()),
                )
            else:
                results = collection.query(
                    query_texts=[query_text],
                    n_results=min(top_k, collection.count()),
                )

            retrieved = []
            if results and results["documents"]:
                for i, docs in enumerate(results["documents"]):
                    for j, doc in enumerate(docs):
                        meta = (
                            results["metadatas"][i][j]
                            if results.get("metadatas")
                            else {}
                        )
                        dist = (
                            results["distances"][i][j]
                            if results.get("distances")
                            else None
                        )
                        retrieved.append(
                            {
                                "template": doc,
                                "typology": meta.get("typology", "unknown"),
                                "source": meta.get("source", "unknown"),
                                "distance": dist,
                            }
                        )

            return retrieved if retrieved else [self._get_default_template()]

        except Exception as e:
            logger.error(f"Template retrieval failed: {e}")
            return [self._get_default_template()]

    def _get_default_template(self) -> dict:
        """Fallback template when ChromaDB is empty."""
        return {
            "template": """SUSPICIOUS ACTIVITY REPORT

SUBJECT INFORMATION:
The subject is a banking customer whose account activity has triggered suspicious activity monitoring alerts.

SUSPICIOUS ACTIVITY DESCRIPTION:
Analysis of the subject's transaction history reveals patterns consistent with potential money laundering activity. The transactions show unusual patterns in terms of velocity, volume, and counterparty relationships that deviate significantly from the customer's established profile.

SUPPORTING EVIDENCE:
- Transaction velocity and volume analysis
- Network analysis of counterparty relationships
- Pattern matching against known typologies

ANALYST ASSESSMENT:
Based on the evidence gathered, the activity warrants filing a Suspicious Activity Report with the Financial Intelligence Unit.""",
            "typology": "general",
            "source": "default_template",
            "distance": None,
        }
