"""
Evaluation pipeline for orchestrating the LLM evaluation process.
"""

from typing import Dict, Any, List, Optional, Union
import pandas as pd
from tqdm import tqdm

from evaluator.metrics.base import Metric
from evaluator.scoring import TrafficLightScorer


class EvaluationPipeline:
    """
    Pipeline for evaluating LLM responses using multiple metrics.

    Orchestrates the application of metrics to a dataset and aggregates results.
    """

    def __init__(self, metrics: List[Metric], scorer: TrafficLightScorer):
        """
        Initialize an evaluation pipeline.

        Args:
            metrics: List of metric objects to use for evaluation
            scorer: TrafficLightScorer to convert raw scores to traffic light statuses
        """
        self.metrics = metrics
        self.scorer = scorer

    def evaluate_single(
        self, question: str, response: str, reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single response using all metrics.

        Args:
            question: The question or prompt given to the LLM
            response: The LLM's response to evaluate
            reference: Optional reference answer

        Returns:
            Dictionary with evaluation results for each metric
        """
        results = {}

        # Track any errors
        errors = []

        # Apply each metric
        for metric in self.metrics:
            try:
                metric_result = metric.evaluate(question, response, reference)

                # Add metric name prefix to each key
                for key, value in metric_result.items():
                    results[f"{metric.name}_{key}"] = value

            except Exception as e:
                errors.append(f"{metric.name}: {str(e)}")

        # Add any errors to results
        if errors:
            results["errors"] = errors

        return results

    def evaluate(self, data: Union[pd.DataFrame, List[Dict[str, str]]]) -> pd.DataFrame:
        """
        Evaluate a dataset of responses.

        Args:
            data: DataFrame or list of dictionaries with columns/keys:
                 - 'question': The question or prompt
                 - 'response': The LLM's response
                 - 'reference': Optional reference answer

        Returns:
            DataFrame with evaluation results for each response
        """
        # Convert list to DataFrame if necessary
        if isinstance(data, list):
            data = pd.DataFrame(data)

        # Ensure required columns exist
        for col in ["question", "response"]:
            if col not in data.columns:
                raise ValueError(f"Required column '{col}' not found in data")

        # Initialize results
        results = []

        # Process each row
        for _, row in tqdm(
            data.iterrows(), total=len(data), desc="Evaluating responses"
        ):
            # Get inputs
            question = row["question"]
            response = row["response"]
            reference = row.get("reference")

            # Evaluate
            row_results = self.evaluate_single(question, response, reference)

            # Add original data
            row_results["question"] = question
            row_results["response"] = response
            if reference is not None:
                row_results["reference"] = reference

            # Add row ID if available
            if "id" in row:
                row_results["id"] = row["id"]

            results.append(row_results)

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Apply traffic light scoring
        scored_df = self.scorer.score_results(results_df)

        return scored_df

    def summarize(self, results: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a summary of evaluation results.

        Args:
            results: DataFrame with evaluation results

        Returns:
            Dictionary with summary statistics
        """
        summary = {}

        # Overall status distribution
        status_counts = results["overall_status"].value_counts().to_dict()
        summary["status_distribution"] = status_counts
        summary["total_evaluated"] = len(results)

        # Average scores per metric
        for metric in self.metrics:
            score_col = f"{metric.name}_score"
            if score_col in results.columns:
                summary[f"avg_{metric.name}_score"] = results[score_col].mean()

        # Count of toxicity
        if "toxicity_is_toxic" in results.columns:
            summary["toxic_count"] = results["toxicity_is_toxic"].sum()

        # Count of missing evaluations
        if "errors" in results.columns:
            summary["errors_count"] = results["errors"].notna().sum()

        return summary
