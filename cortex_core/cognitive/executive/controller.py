"""
Executive Controller (Prefrontal Cortex).
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExecutiveController:
    """
    Executive decision-making controller.

    Makes final decisions based on integrated analysis.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.decision_threshold = config.get("decision_threshold", 0.7)

        logger.info("Executive Controller initialized")

    def decide(self, fused_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make executive decision.

        Args:
            fused_results: Results from fusion controller

        Returns:
            Final decision
        """
        try:
            # Analyze confidence levels
            confidence = fused_results.get("integration_confidence", 0.0)

            # Make decision based on confidence
            if confidence >= self.decision_threshold:
                decision = "PROCEED"
            else:
                decision = "REVIEW_REQUIRED"

            # Add context to decision
            analysis_count = len(fused_results.get("analysis", []))
            insights_count = len(fused_results.get("resolved_insights", []))

            decision_details = {
                "decision": decision,
                "confidence": confidence,
                "threshold": self.decision_threshold,
                "analysis_points": analysis_count,
                "insights_processed": insights_count,
                "reasoning": self._generate_reasoning(fused_results),
            }

            logger.info(f"Executive decision: {decision} (confidence: {
                    confidence:.2f})")

            return decision_details

        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            return {
                "decision": "ERROR",
                "confidence": 0.0,
                "threshold": self.decision_threshold,
                "analysis_points": 0,
                "insights_processed": 0,
                "reasoning": f"Decision failed: {str(e)}",
            }

    def _generate_reasoning(self, fused_results: Dict[str, Any]) -> str:
        """Generate reasoning for decision."""
        confidence = fused_results.get("integration_confidence", 0.0)

        if confidence >= self.decision_threshold:
            return "High confidence in analysis results"
        else:
            return "Additional review recommended due to lower confidence"

    def is_healthy(self) -> bool:
        """Check if controller is healthy."""
        return True
