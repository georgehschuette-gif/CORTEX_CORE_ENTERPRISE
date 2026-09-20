"""
Divergent thinking for generating multiple perspectives.
"""

import random
from typing import Any, Dict, List


class DivergentThinking:
    """
    Divergent thinking engine for exploring multiple solution paths.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.perspective_filters = [
            "optimistic",
            "pessimistic",
            "neutral",
            "extreme",
            "minimalist",
            "maximalist",
        ]

    def generate_perspectives(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple perspectives on a problem.

        Args:
            problem: Problem description

        Returns:
            List of different perspectives
        """
        perspectives = []

        for filter_type in self.perspective_filters:
            perspective = self._apply_perspective_filter(problem, filter_type)
            perspectives.append(perspective)

        return perspectives

    def brainstorm_solutions(
        self, problem: Dict[str, Any], num_solutions: int = 10
    ) -> List[str]:
        """
        Generate multiple solution ideas.

        Args:
            problem: Problem description
            num_solutions: Number of solutions to generate

        Returns:
            List of solution ideas
        """
        solutions = []

        for _ in range(num_solutions):
            solution = self._generate_random_solution(problem)
            solutions.append(solution)

        return solutions

    def _apply_perspective_filter(
        self, problem: Dict[str, Any], filter_type: str
    ) -> Dict[str, Any]:
        """Apply a perspective filter to the problem."""
        filtered_problem = problem.copy()

        if filter_type == "optimistic":
            filtered_problem["description"] = (
                "What are the best possible outcomes for: "
                + problem.get("description", "")
            )
            filtered_problem["approach"] = "focus on opportunities and positive aspects"

        elif filter_type == "pessimistic":
            filtered_problem["description"] = f"What could go wrong with: {
                problem.get(
                    'description', '')}"
            filtered_problem["approach"] = "identify risks and failure modes"

        elif filter_type == "extreme":
            filtered_problem["description"] = f"Take {
                problem.get(
                    'description',
                    '')} to the extreme"
            filtered_problem["approach"] = "exaggerate and amplify all aspects"

        elif filter_type == "minimalist":
            filtered_problem["description"] = f"What's the simplest version of: {
                problem.get(
                    'description',
                    '')}"
            filtered_problem["approach"] = "remove complexity and focus on essentials"

        else:
            filtered_problem["approach"] = f"apply {filter_type} perspective"

        return {
            "filter": filter_type,
            "problem": filtered_problem,
            "generated_at": "2024-01-15T10:30:00Z",
        }

    def _generate_random_solution(self, problem: Dict[str, Any]) -> str:
        """Generate a random solution idea."""
        solution_templates = [
            "Combine {concept1} with {concept2}",
            "Remove {concept1} and replace with {concept2}",
            "Reverse the order of {concept1}",
            "Make {concept1} much larger",
            "Make {concept1} much smaller",
            "Change the location of {concept1}",
            "Change the timing of {concept1}",
            "Add a constraint to {concept1}",
            "Remove a constraint from {concept1}",
            "Copy {concept1} from another domain",
        ]

        # Extract concepts from problem
        concepts = self._extract_concepts(problem)

        if len(concepts) >= 2:
            concept1, concept2 = random.sample(concepts, 2)
        elif len(concepts) == 1:
            concept1 = concepts[0]
            concept2 = "something unexpected"
        else:
            concept1 = "the core problem"
            concept2 = "an innovative approach"

        template = random.choice(solution_templates)
        solution = template.format(concept1=concept1, concept2=concept2)

        return solution

    def _extract_concepts(self, problem: Dict[str, Any]) -> List[str]:
        """Extract key concepts from problem description."""
        concepts = []

        description = problem.get("description", "")
        words = description.lower().split()

        # Simple concept extraction - nouns and important terms
        important_words = ["system", "process", "data", "user", "problem", "solution"]

        for word in words:
            if len(word) > 3 and word not in ["that", "this", "with", "from", "have"]:
                concepts.append(word)

        # Add important words if not present
        for word in important_words:
            if word in description.lower():
                concepts.append(word)

        return list(set(concepts)) if concepts else ["general problem"]
