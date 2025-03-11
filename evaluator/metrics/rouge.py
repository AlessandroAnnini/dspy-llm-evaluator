"""
ROUGE metric for evaluating text overlap between response and reference.
"""

from typing import Dict, Any, Optional
import re

try:
    from rouge import Rouge
except ImportError:
    raise ImportError("Please install the rouge package: pip install rouge")

from evaluator.metrics.base import Metric


class RougeMetric(Metric):
    """
    Metric that evaluates text overlap between a response and a reference answer.

    Uses the rouge library to calculate ROUGE-1, ROUGE-2, and ROUGE-L scores.
    """

    def __init__(self, name: Optional[str] = None):
        """Initialize RougeMetric."""
        super().__init__(name)
        self.rouge = Rouge()

    def evaluate(
        self, question: str, response: str, reference: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate text overlap between response and reference using ROUGE metrics.

        Args:
            question: The question or prompt given to the LLM (not used for ROUGE)
            response: The LLM's response to evaluate
            reference: Reference answer to compare against

        Returns:
            Dict with:
            - 'score': Average F1 score across ROUGE-1, ROUGE-2, and ROUGE-L (float 0-1)
            - 'rouge_1_f': ROUGE-1 F1 score
            - 'rouge_2_f': ROUGE-2 F1 score
            - 'rouge_l_f': ROUGE-L F1 score
            - 'explanation': Brief explanation of the ROUGE scores
        """
        self.validate_inputs(question, response, reference)

        if not reference:
            return {
                "score": 0.0,
                "explanation": "Cannot calculate ROUGE score without a reference answer",
            }

        if not response.strip():
            return {"score": 0.0, "explanation": "Empty response"}

        try:
            # Clean text (remove excess whitespace)
            response_clean = re.sub(r"\s+", " ", response).strip()
            reference_clean = re.sub(r"\s+", " ", reference).strip()

            # Calculate ROUGE scores
            scores = self.rouge.get_scores(response_clean, reference_clean)[0]

            # Extract F1 scores
            rouge_1_f = scores["rouge-1"]["f"]
            rouge_2_f = scores["rouge-2"]["f"]
            rouge_l_f = scores["rouge-l"]["f"]

            # Compute average F1 score as the main metric
            avg_f1 = (rouge_1_f + rouge_2_f + rouge_l_f) / 3.0

            # Create explanation
            explanation = (
                f"ROUGE-1 F1: {rouge_1_f:.3f}, "
                f"ROUGE-2 F1: {rouge_2_f:.3f}, "
                f"ROUGE-L F1: {rouge_l_f:.3f}. "
                f"Average F1: {avg_f1:.3f}."
            )

            return {
                "score": avg_f1,
                "rouge_1_f": rouge_1_f,
                "rouge_2_f": rouge_2_f,
                "rouge_l_f": rouge_l_f,
                "explanation": explanation,
            }
        except Exception as e:
            return {
                "score": 0.0,
                "explanation": f"Error calculating ROUGE score: {str(e)}",
            }
