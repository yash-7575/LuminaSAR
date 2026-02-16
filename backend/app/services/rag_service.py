"""
Hybrid RAG Service — Chroma Templates + FAISS Historical Similarity

Combines:
1. Regulatory template retrieval (ChromaDB)
2. Historical SAR similarity search (FAISS)

Used in LuminaSAR for grounded, explainable SAR generation.
"""

import os
import logging
from typing import List, Dict

import chromadb
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("luminasar.rag_service")


class RAGService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        # ------------------------
        # Chroma (Templates)
        # ------------------------
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

        # ------------------------
        # FAISS (Historical SARs)
        # ------------------------
        self.faiss_index = None
        self.faiss_texts = None

        # Shared embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        self._load_faiss()

    # ======================================================
    # FAISS SECTION
    # ======================================================

    def _load_faiss(self):
        """Load FAISS index + stored texts."""
        try:
            base_path = os.path.join(os.getcwd(), "data", "rag")
            index_path = os.path.join(base_path, "rag_fast.faiss")
            texts_path = os.path.join(base_path, "rag_texts_fast.npy")

            if os.path.exists(index_path) and os.path.exists(texts_path):
                self.faiss_index = faiss.read_index(index_path)
                self.faiss_texts = np.load(texts_path, allow_pickle=True)
                logger.info(
                    f"✅ FAISS loaded with {self.faiss_index.ntotal} vectors"
                )
            else:
                logger.warning("⚠️ FAISS files not found. Similarity disabled.")

        except Exception as e:
            logger.error(f"❌ FAISS loading failed: {e}")

    def retrieve_similar_cases(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve similar historical SAR cases from FAISS."""
        if not self.faiss_index:
            return []

        try:
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.faiss_index.search(
                query_embedding.astype("float32"), top_k
            )

            results = []
            for idx in indices[0]:
                if idx < len(self.faiss_texts):
                    results.append(self.faiss_texts[idx])

            return results

        except Exception as e:
            logger.error(f"FAISS retrieval failed: {e}")
            return []

    # ======================================================
    # CHROMA TEMPLATE SECTION
    # ======================================================

    def _get_client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name="sar_templates",
                metadata={
                    "description": "SAR templates and regulatory guidelines"
                },
            )
        return self._collection

    def load_templates(self, templates_dir: str) -> int:
        """Load template text files into Chroma."""
        from pathlib import Path

        templates_path = Path(templates_dir)
        if not templates_path.exists():
            logger.warning("Templates directory not found.")
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
                    metadatas.append({"source": file_path.name})
                    ids.append(f"template_{i}")

            except Exception as e:
                logger.warning(f"Failed to load template: {e}")

        if documents:
            collection = self._get_collection()
            embeddings = self.embedding_model.encode(documents).tolist()

            collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"✅ Loaded {len(documents)} templates into Chroma")

        return len(documents)

    def retrieve_templates(
        self, typologies: List[str], top_k: int = 3
    ) -> List[Dict]:
        """Retrieve structural templates from Chroma."""
        try:
            collection = self._get_collection()

            if collection.count() == 0:
                logger.warning("⚠️ Chroma empty — returning default template")
                return [self._get_default_template()]

            query_text = (
                f"SAR narrative template for {', '.join(typologies)} "
                f"money laundering suspicious activity"
            )

            query_embedding = self.embedding_model.encode([query_text]).tolist()

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k, collection.count()),
            )

            retrieved = []
            if results and results["documents"]:
                for i, docs in enumerate(results["documents"]):
                    for j, doc in enumerate(docs):
                        retrieved.append(
                            {
                                "template": doc,
                                "source": results["metadatas"][i][j]["source"],
                            }
                        )

            return retrieved if retrieved else [self._get_default_template()]

        except Exception as e:
            logger.error(f"Template retrieval failed: {e}")
            return [self._get_default_template()]

    def _get_default_template(self):
        return {
            "template": "Standard SAR regulatory structure template.",
            "source": "default_template",
        }

    # ======================================================
    # HYBRID RETRIEVAL
    # ======================================================

    def retrieve_hybrid_context(
        self, typologies: List[str], patterns: Dict
    ) -> Dict:
        """
        Combines:
        - Chroma structural templates
        - FAISS similar historical SARs
        """

        templates = self.retrieve_templates(typologies)

        query = (
            f"Risk score {patterns.get('risk_score', 0)}, "
            f"typologies: {', '.join(typologies)}"
        )

        similar_cases = self.retrieve_similar_cases(query)

        return {
            "templates": templates,
            "similar_cases": similar_cases,
        }
