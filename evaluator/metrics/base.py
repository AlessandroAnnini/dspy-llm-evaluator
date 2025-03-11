"""
Base class for all evaluation metrics in the LLM Evaluator.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

import dspy


class Metric(ABC):
    """
    Abstract base class for all evaluation metrics.

    All metrics should inherit from this class and implement the evaluate method.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize a metric.

        Args:
            name: Optional name for the metric. If not provided, will use the class name.
        """
        self.name = name or self.__class__.__name__.lower().replace("metric", "")

    @abstractmethod
    def evaluate(
        self, question: str, response: str, reference: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate a response against a question and optionally a reference answer.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Optional reference or ground truth answer
            **kwargs: Additional parameters that might be needed for specific metrics

        Returns:
            Dictionary containing at minimum a 'score' key with a float value between 0 and 1,
            except for toxicity which should return a boolean under 'is_toxic'.
            May include additional information under other keys.
        """
        pass

    def validate_inputs(
        self, question: str, response: str, reference: Optional[str] = None
    ) -> None:
        """
        Validate inputs to the evaluate method.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Optional reference or ground truth answer

        Raises:
            ValueError: If any inputs are invalid
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")

        if not isinstance(response, str):
            raise ValueError("Response must be a string")

        if reference is not None and not isinstance(reference, str):
            raise ValueError("Reference must be a string or None")


class DSPyMetric(Metric):
    """
    Base class for metrics that use DSPy for evaluation.
    """

    def __init__(self, name: Optional[str] = None):
        """Initialize DSPy-based metric."""
        super().__init__(name)
        self.program = self.build_dspy_program()

    @abstractmethod
    def build_dspy_program(self) -> dspy.Module:
        """
        Build and return a DSPy program for this metric.

        Returns:
            A configured DSPy Module that can be used for evaluation
        """
        pass
