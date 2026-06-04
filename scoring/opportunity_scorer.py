"""Opportunity scoring system with configurable weights."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from core.config import settings


@dataclass
class ScoringWeights:
    profit_potential: float = 0.25
    difficulty: float = 0.10      # Higher = easier (inverted difficulty)
    startup_cost: float = 0.10    # Higher = cheaper
    time_required: float = 0.10   # Higher = faster
    automation_potential: float = 0.20
    scalability: float = 0.15
    risk_level: float = 0.10      # Higher = safer


DEFAULT_WEIGHTS = ScoringWeights()


class OpportunityScorer:
    """
    Scores opportunities 0-100 using weighted dimensions.
    All input dimensions should already be normalised to 0-100.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def compute_score(self, opportunity: Dict) -> float:
        w = self.weights
        raw = (
            self._get(opportunity, "profit_potential") * w.profit_potential
            + self._get(opportunity, "difficulty") * w.difficulty
            + self._get(opportunity, "startup_cost") * w.startup_cost
            + self._get(opportunity, "time_required") * w.time_required
            + self._get(opportunity, "automation_potential") * w.automation_potential
            + self._get(opportunity, "scalability") * w.scalability
            + self._get(opportunity, "risk_level") * w.risk_level
        )
        return round(min(max(raw, 0), 100), 2)

    def score_batch(self, opportunities: list) -> list:
        return sorted(
            [dict(opp, overall_score=self.compute_score(opp)) for opp in opportunities],
            key=lambda x: x["overall_score"],
            reverse=True,
        )

    def meets_threshold(self, opportunity: Dict) -> bool:
        score = self.compute_score(opportunity)
        return score >= settings.opportunity_score_threshold

    def generate_scorecard(self, opportunity: Dict) -> Dict:
        score = self.compute_score(opportunity)
        return {
            "title": opportunity.get("title", "Unknown"),
            "overall_score": score,
            "meets_threshold": score >= settings.opportunity_score_threshold,
            "threshold": settings.opportunity_score_threshold,
            "breakdown": {
                "profit_potential": {
                    "raw": self._get(opportunity, "profit_potential"),
                    "weighted": round(self._get(opportunity, "profit_potential") * self.weights.profit_potential, 2),
                },
                "difficulty": {
                    "raw": self._get(opportunity, "difficulty"),
                    "weighted": round(self._get(opportunity, "difficulty") * self.weights.difficulty, 2),
                },
                "startup_cost": {
                    "raw": self._get(opportunity, "startup_cost"),
                    "weighted": round(self._get(opportunity, "startup_cost") * self.weights.startup_cost, 2),
                },
                "time_required": {
                    "raw": self._get(opportunity, "time_required"),
                    "weighted": round(self._get(opportunity, "time_required") * self.weights.time_required, 2),
                },
                "automation_potential": {
                    "raw": self._get(opportunity, "automation_potential"),
                    "weighted": round(self._get(opportunity, "automation_potential") * self.weights.automation_potential, 2),
                },
                "scalability": {
                    "raw": self._get(opportunity, "scalability"),
                    "weighted": round(self._get(opportunity, "scalability") * self.weights.scalability, 2),
                },
                "risk_level": {
                    "raw": self._get(opportunity, "risk_level"),
                    "weighted": round(self._get(opportunity, "risk_level") * self.weights.risk_level, 2),
                },
            },
            "grade": self._grade(score),
            "recommendation": self._recommendation(opportunity, score),
        }

    @staticmethod
    def _get(opp: Dict, key: str) -> float:
        return float(opp.get(key, 50))

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 85:
            return "A+"
        if score >= 75:
            return "A"
        if score >= 65:
            return "B"
        if score >= 55:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    @staticmethod
    def _recommendation(opp: Dict, score: float) -> str:
        if score >= 80:
            return "Strong approve — prioritise for immediate execution"
        if score >= 65:
            return "Approve — include in execution pipeline"
        if score >= 50:
            return "Hold — needs validation or improvement before proceeding"
        return "Reject — does not meet minimum criteria"
