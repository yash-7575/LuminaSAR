"""Pattern Detection Service — ML-based suspicious activity pattern detection.

Analyzes transaction data to detect money laundering patterns including:
- Velocity analysis (rapid money movement)
- Volume analysis (unusual amounts)
- Structuring detection (amounts just below reporting threshold)
- Network analysis (graph-based source/destination analysis)
- Typology matching (layering, structuring, smurfing, integration)
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger("luminasar.pattern_detector")


class PatternDetector:
    """Detects suspicious transaction patterns using ML and statistical analysis."""

    def __init__(self):
        self.threshold_structuring = 50000  # ₹50K CTR threshold

    def analyze(self, transactions_df: pd.DataFrame) -> dict:
        """Master function that runs all detection algorithms.

        Args:
            transactions_df: DataFrame with columns: transaction_id, amount, date,
                           source_account, destination_account

        Returns:
            Dictionary containing all patterns, typologies, and risk score.
        """
        if transactions_df.empty:
            return {
                "velocity": {
                    "time_span_days": 0,
                    "transactions_per_day": 0,
                    "risk": "LOW",
                },
                "volume": {
                    "total_amount": 0,
                    "avg_amount": 0,
                    "max_amount": 0,
                    "num_transactions": 0,
                },
                "structuring": {
                    "near_threshold_count": 0,
                    "structuring_likelihood": 0,
                    "suspicious": False,
                },
                "network": {
                    "unique_sources": 0,
                    "unique_destinations": 0,
                    "fan_in_high": False,
                    "fan_out_high": False,
                },
                "typologies": [],
                "risk_score": 0.0,
            }

        # Ensure date column is datetime
        if "date" in transactions_df.columns:
            transactions_df["date"] = pd.to_datetime(
                transactions_df["date"], errors="coerce"
            )

        # Ensure amount is numeric
        transactions_df["amount"] = pd.to_numeric(
            transactions_df["amount"], errors="coerce"
        )

        patterns = {
            "velocity": self.analyze_velocity(transactions_df),
            "volume": self.analyze_volume(transactions_df),
            "structuring": self.detect_structuring(transactions_df),
            "network": self.analyze_network(transactions_df),
            "typologies": [],
            "risk_score": 0.0,
        }

        # Match to typologies
        patterns["typologies"] = self.match_typologies(patterns)
        patterns["risk_score"] = self.calculate_risk_score(patterns)

        logger.info(
            f"Pattern analysis complete: risk={patterns['risk_score']}, "
            f"typologies={patterns['typologies']}"
        )

        return patterns

    def analyze_velocity(self, df: pd.DataFrame) -> dict:
        """Detect rapid money movement — time-based analysis."""
        date_col = df["date"].dropna()

        if date_col.empty:
            return {"time_span_days": 0, "transactions_per_day": 0, "risk": "LOW"}

        time_span_days = (date_col.max() - date_col.min()).days
        transactions_per_day = len(df) / max(time_span_days, 1)

        if time_span_days < 7:
            risk = "HIGH"
        elif time_span_days < 30:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "time_span_days": int(time_span_days),
            "transactions_per_day": round(transactions_per_day, 2),
            "risk": risk,
        }

    def analyze_volume(self, df: pd.DataFrame) -> dict:
        """Analyze transaction volumes for anomalies."""
        amounts = df["amount"].dropna()

        if amounts.empty:
            return {
                "total_amount": 0,
                "avg_amount": 0,
                "max_amount": 0,
                "num_transactions": 0,
            }

        return {
            "total_amount": round(float(amounts.sum()), 2),
            "avg_amount": round(float(amounts.mean()), 2),
            "max_amount": round(float(amounts.max()), 2),
            "num_transactions": len(df),
        }

    def detect_structuring(self, df: pd.DataFrame) -> dict:
        """Detect structuring — amounts deliberately kept just below threshold."""
        threshold = self.threshold_structuring
        amounts = df["amount"].dropna()

        if amounts.empty:
            return {
                "near_threshold_count": 0,
                "structuring_likelihood": 0.0,
                "suspicious": False,
            }

        # Find transactions between 90-100% of threshold
        near_threshold = amounts[(amounts >= threshold * 0.90) & (amounts < threshold)]

        structuring_likelihood = (
            len(near_threshold) / len(amounts) if len(amounts) > 0 else 0
        )

        return {
            "near_threshold_count": int(len(near_threshold)),
            "structuring_likelihood": round(structuring_likelihood, 3),
            "suspicious": structuring_likelihood > 0.3,
        }

    def analyze_network(self, df: pd.DataFrame) -> dict:
        """Build transaction network graph and analyze topology."""
        try:
            import networkx as nx

            G = nx.DiGraph()

            for _, row in df.iterrows():
                src = str(row.get("source_account", "unknown"))
                dst = str(row.get("destination_account", "unknown"))
                amt = float(row.get("amount", 0))
                G.add_edge(src, dst, amount=amt)

            unique_sources = len(set(df["source_account"].dropna().unique()))
            unique_destinations = len(set(df["destination_account"].dropna().unique()))

            # Detect hub nodes (high degree centrality)
            hub_detected = False
            if G.number_of_nodes() > 0:
                centrality = nx.degree_centrality(G)
                max_centrality = max(centrality.values()) if centrality else 0
                hub_detected = max_centrality > 0.5

            return {
                "unique_sources": unique_sources,
                "unique_destinations": unique_destinations,
                "fan_in_high": unique_sources > 20,
                "fan_out_high": unique_destinations > 20,
                "hub_detected": hub_detected,
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
            }
        except Exception as e:
            logger.warning(f"Network analysis failed: {e}")
            return {
                "unique_sources": 0,
                "unique_destinations": 0,
                "fan_in_high": False,
                "fan_out_high": False,
                "hub_detected": False,
                "total_nodes": 0,
                "total_edges": 0,
            }

    def match_typologies(self, patterns: dict) -> list:
        """Match detected patterns to money laundering typologies."""
        typologies = []

        velocity = patterns.get("velocity", {})
        network = patterns.get("network", {})
        structuring = patterns.get("structuring", {})
        volume = patterns.get("volume", {})

        # Layering: rapid movement + many distinct sources
        if (
            velocity.get("time_span_days", 999) < 7
            and network.get("unique_sources", 0) > 5
        ):
            typologies.append("layering")

        # Structuring: many near-threshold amounts
        if structuring.get("suspicious", False):
            typologies.append("structuring")

        # Smurfing: many unique sources feeding into few destinations
        if network.get("unique_sources", 0) > 15:
            typologies.append("smurfing")

        # Integration: large volume in short time
        if (
            volume.get("total_amount", 0) > 5000000
            and velocity.get("time_span_days", 999) < 14
        ):
            typologies.append("integration")

        # Round-tripping: high fan-in AND fan-out
        if network.get("fan_in_high", False) and network.get("fan_out_high", False):
            typologies.append("round_tripping")

        # Funnel account: very high hub centrality
        if network.get("hub_detected", False):
            typologies.append("funnel_account")

        if not typologies:
            typologies.append("general_suspicious")

        return typologies

    def calculate_risk_score(self, patterns: dict) -> float:
        """Calculate risk score from 0 to 10."""
        score = 0.0

        velocity = patterns.get("velocity", {})
        volume = patterns.get("volume", {})
        structuring = patterns.get("structuring", {})
        network = patterns.get("network", {})

        # Velocity risk (0-30 points)
        if velocity.get("time_span_days", 999) < 7:
            score += 30
        elif velocity.get("time_span_days", 999) < 30:
            score += 15
        elif velocity.get("transactions_per_day", 0) > 5:
            score += 10

        # Volume risk (0-25 points)
        total = volume.get("total_amount", 0)
        if total > 10000000:
            score += 25
        elif total > 5000000:
            score += 18
        elif total > 1000000:
            score += 10

        # Structuring risk (0-25 points)
        likelihood = structuring.get("structuring_likelihood", 0)
        score += likelihood * 25

        # Network risk (0-20 points)
        if network.get("fan_in_high", False) or network.get("fan_out_high", False):
            score += 15
        if network.get("hub_detected", False):
            score += 5

        return min(round(score / 10, 1), 10.0)
