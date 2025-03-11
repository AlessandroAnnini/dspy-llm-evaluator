"""
Relevancy metric for evaluating how well a response addresses the question.
"""

from typing import Dict, Any, Optional

import dspy

from evaluator.metrics.base import DSPyMetric


class RelevancySignature(dspy.Signature):
    """Signature for the relevancy evaluation DSPy program."""

    question = dspy.InputField(desc="The question or prompt given to the LLM")
    response = dspy.InputField(desc="The LLM's response to evaluate for relevancy")

    score = dspy.OutputField(
        desc="Relevancy score from 0 to 1, where 1 is perfectly relevant"
    )
    explanation = dspy.OutputField(desc="Brief explanation for the relevancy score")


class RelevancyProgram(dspy.Module):
    """
    DSPy program for evaluating the relevancy of a response to a question.
    """

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(RelevancySignature)

    def forward(self, question: str, response: str) -> Dict[str, Any]:
        """
        Evaluate the relevancy of a response to a question.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate

        Returns:
            Dict with 'score' and 'explanation'
        """
        result = self.predictor(question=question, response=response)

        # Ensure score is a float between 0 and 1
        try:
            score = float(result.score)
            score = max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            score = 0.0

        return {"score": score, "explanation": result.explanation}


class RelevancyMetric(DSPyMetric):
    """
    Metric that evaluates how well a response addresses the question.

    Uses DSPy to generate a relevancy score by comparing the question and response.
    """

    def build_dspy_program(self) -> dspy.Module:
        """Build the DSPy program for relevancy evaluation."""
        return RelevancyProgram()

    def evaluate(
        self, question: str, response: str, reference: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate the relevancy of a response to a question.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Optional reference answer (not used for relevancy)

        Returns:
            Dict with 'score' (float 0-1) and 'explanation'
        """
        self.validate_inputs(question, response)

        if not response.strip():
            return {"score": 0.0, "explanation": "Empty response"}

        try:
            result = self.program(question, response)
            return result
        except Exception as e:
            return {
                "score": 0.0,
                "explanation": f"Error evaluating relevancy: {str(e)}",
            }
