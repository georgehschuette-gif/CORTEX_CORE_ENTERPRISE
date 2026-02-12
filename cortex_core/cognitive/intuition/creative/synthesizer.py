"""
Creative synthesizer for generating novel insights.
"""

import random
from typing import Dict, Any, List


class Synthesizer:
    """
    Creative synthesizer for generating novel connections and insights.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.creativity_patterns = [
            "analogical_reasoning",
            "lateral_thinking",
            "combinatorial_creativity",
            "perspective_shifting"
        ]

    def synthesize(self, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize creative insights from inputs.

        Args:
            inputs: List of input data

        Returns:
            Creative synthesis results
        """
        if not inputs:
            return {'insights': [], 'novelty_score': 0.0}

        # Apply different creativity techniques
        insights = []

        # Analogical reasoning
        analogies = self._analogical_reasoning(inputs)
        insights.extend(analogies)

        # Lateral thinking
        lateral = self._lateral_thinking(inputs)
        insights.extend(lateral)

        # Combinatorial creativity
        combinations = self._combinatorial_creativity(inputs)
        insights.extend(combinations)

        # Calculate novelty
        novelty_score = self._calculate_novelty(insights)

        return {
            'insights': insights,
            'novelty_score': novelty_score,
            'techniques_used': self.creativity_patterns
        }

    def _analogical_reasoning(self, inputs: List[Dict[str, Any]]) -> List[str]:
        """Apply analogical reasoning."""
        insights = []

        # Find similar patterns across different domains
        for i, input1 in enumerate(inputs):
            for j, input2 in enumerate(inputs[i + 1:], i + 1):
                similarity = self._calculate_similarity(input1, input2)
                if similarity > 0.3:  # Threshold for analogy
                    insight = f"Analogous to {
                        input1.get(
                            'type',
                            'unknown')}: {
                        input2.get(
                            'type',
                            'unknown')} exhibits similar patterns"
                    insights.append(insight)

        return insights

    def _lateral_thinking(self, inputs: List[Dict[str, Any]]) -> List[str]:
        """Apply lateral thinking techniques."""
        insights = []

        # Challenge assumptions
        for input_data in inputs:
            assumptions = self._identify_assumptions(input_data)
            for assumption in assumptions:
                insight = f"Lateral perspective: What if {assumption} were not true?"
                insights.append(insight)

        return insights

    def _combinatorial_creativity(
            self, inputs: List[Dict[str, Any]]) -> List[str]:
        """Apply combinatorial creativity."""
        insights = []

        if len(inputs) >= 2:
            # Combine elements from different inputs
            for i in range(min(3, len(inputs))):  # Limit combinations
                combo_inputs = random.sample(inputs, min(3, len(inputs)))
                combination = " + ".join([str(inp.get('type', 'unknown'))
                                         for inp in combo_inputs])
                insight = f"Creative combination: {combination} could yield novel approaches"
                insights.append(insight)

        return insights

    def _calculate_similarity(
            self, input1: Dict[str, Any], input2: Dict[str, Any]) -> float:
        """Calculate similarity between inputs."""
        # Simple similarity based on shared keys and types
        keys1 = set(input1.keys())
        keys2 = set(input2.keys())

        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _identify_assumptions(self, input_data: Dict[str, Any]) -> List[str]:
        """Identify assumptions in input data."""
        assumptions = []

        # Common assumptions based on data patterns
        if 'priority' in input_data:
            assumptions.append("priority levels are fixed")

        if 'type' in input_data:
            assumptions.append(f"{input_data['type']} is well-defined")

        if isinstance(input_data.get('data'), dict):
            assumptions.append("data structure is stable")

        return assumptions

    def _calculate_novelty(self, insights: List[str]) -> float:
        """Calculate novelty score of insights."""
        if not insights:
            return 0.0

        # Simple novelty measure
        unique_concepts = set()
        total_words = 0

        for insight in insights:
            words = insight.lower().split()
            unique_concepts.update(words)
            total_words += len(words)

        if total_words == 0:
            return 0.0

        return len(unique_concepts) / total_words
