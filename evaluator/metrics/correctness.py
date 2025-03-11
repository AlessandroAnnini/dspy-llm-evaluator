"""
Correctness metric for evaluating factual accuracy of a response.
"""

from typing import Dict, Any, Optional

import dspy

from evaluator.metrics.base import DSPyMetric


class CorrectnessSignature(dspy.Signature):
    """Signature for the correctness evaluation DSPy program."""

    question = dspy.InputField(desc="The question or prompt given to the LLM")
    response = dspy.InputField(
        desc="The LLM's response to evaluate for factual correctness"
    )
    reference = dspy.InputField(
        desc="Reference answer to compare against (ground truth)"
    )

    score = dspy.OutputField(
        desc="Correctness score from 0 to 1, where 1 is completely correct"
    )
    explanation = dspy.OutputField(
        desc="Brief explanation for the correctness score, highlighting any factual errors"
    )


class CorrectnessProgram(dspy.Module):
    """
    DSPy program for evaluating the factual correctness of a response.
    """

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(CorrectnessSignature)

    def forward(self, question: str, response: str, reference: str) -> Dict[str, Any]:
        """
        Evaluate the factual correctness of a response using a reference answer.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Reference answer (ground truth)

        Returns:
            Dict with 'score' and 'explanation'
        """
        result = self.predictor(
            question=question, response=response, reference=reference
        )

        # Ensure score is a float between 0 and 1
        try:
            score = float(result.score)
            score = max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            score = 0.0

        return {"score": score, "explanation": result.explanation}


class CorrectnessMetric(DSPyMetric):
    """
    Metric that evaluates the factual correctness of a response.

    Uses DSPy to generate a correctness score by comparing the response
    against a reference answer.
    """

    def build_dspy_program(self) -> dspy.Module:
        """Build the DSPy program for correctness evaluation."""
        return CorrectnessProgram()

    def evaluate(
        self, question: str, response: str, reference: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate the factual correctness of a response.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Reference answer (ground truth)

        Returns:
            Dict with 'score' (float 0-1) and 'explanation'
        """
        self.validate_inputs(question, response, reference)

        if not reference:
            return {
                "score": 0.0,
                "explanation": "Cannot evaluate correctness without a reference answer",
            }

        if not response.strip():
            return {"score": 0.0, "explanation": "Empty response"}

        try:
            result = self.program(question, response, reference)
            return result
        except Exception as e:
            return {
                "score": 0.0,
                "explanation": f"Error evaluating correctness: {str(e)}",
            }
