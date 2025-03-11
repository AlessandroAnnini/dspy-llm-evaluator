"""
Metrics for evaluating LLM responses

This module provides metric classes for evaluating different aspects of LLM responses:
- RelevancyMetric: Assesses how well a response addresses the question
- CorrectnessMetric: Evaluates factual accuracy of a response
- RougeMetric: Measures text overlap between response and reference
- ToxicityMetric: Detects harmful or inappropriate content
"""

from evaluator.metrics.base import Metric
from evaluator.metrics.relevancy import RelevancyMetric
from evaluator.metrics.correctness import CorrectnessMetric
from evaluator.metrics.rouge import RougeMetric
from evaluator.metrics.toxicity import ToxicityMetric

__all__ = [
    "Metric",
    "RelevancyMetric",
    "CorrectnessMetric",
    "RougeMetric",
    "ToxicityMetric",
]
