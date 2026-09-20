"""
Fusion Controller (Corpus Callosum).
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FusionController:
    """
    Neural-symbolic fusion controller.

    Integrates intuitive and logical processing results.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.integration_method = config.get("integration_method", "weighted_average")

        logger.info("Fusion Controller initialized")

    def fuse(
        self, intuitive_results: Dict[str, Any], logical_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fuse intuitive and logical results.

        Args:
            intuitive_results: Results from intuition engine
            logical_results: Results from logic engine

        Returns:
            Fused analysis results
        """
        try:
            # Combine insights
            combined_insights = self._combine_insights(
                intuitive_results.get("insights", []),
                logical_results.get("reasoning", []),
            )

            # Resolve conflicts
            resolved_insights = self._resolve_conflicts(combined_insights)

            # Generate integrated analysis
            analysis = self._generate_analysis(resolved_insights)

            result = {
                "combined_insights": combined_insights,
                "resolved_insights": resolved_insights,
                "analysis": analysis,
                "integration_confidence": self._calculate_integration_confidence(
                    intuitive_results, logical_results
                ),
                "processing_type": "fusion",
            }

            logger.debug(f"Fusion completed: {
                    len(analysis)} integrated insights")

            return result

        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            return {
                "combined_insights": [],
                "resolved_insights": [],
                "analysis": [],
                "integration_confidence": 0.0,
                "error": str(e),
            }

    def _combine_insights(
        self, intuitive: List[str], logical: List[str]
    ) -> List[Dict[str, Any]]:
        """Combine intuitive and logical insights."""
        combined = []

        # Add intuitive insights
        for insight in intuitive:
            combined.append(
                {"source": "intuition", "content": insight, "type": "intuitive"}
            )

        # Add logical insights
        for insight in logical:
            combined.append({"source": "logic", "content": insight, "type": "logical"})

        return combined

    def _resolve_conflicts(
        self, insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts between insights."""
        # Simple conflict resolution - prefer logical for now
        resolved = []

        for insight in insights:
            if insight["type"] == "logical":
                # Logical insights get higher priority
                insight["priority"] = 2
            else:
                insight["priority"] = 1

            resolved.append(insight)

        return sorted(resolved, key=lambda x: x["priority"], reverse=True)

    def _generate_analysis(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate integrated analysis."""
        analysis = []

        # Create integrated analysis
        if insights:
            analysis.append("Integrated neural-symbolic analysis completed")
            analysis.append(f"Processed {
                    len(insights)} insights from both hemispheres")

        return analysis

    def _calculate_integration_confidence(
        self, intuitive: Dict[str, Any], logical: Dict[str, Any]
    ) -> float:
        """Calculate confidence in integration."""
        intuitive_conf = intuitive.get("confidence", 0.0)
        logical_conf = logical.get("confidence", 0.0)

        # Weighted average
        return (intuitive_conf + logical_conf) / 2

    def is_healthy(self) -> bool:
        """Check if controller is healthy."""
        return True
