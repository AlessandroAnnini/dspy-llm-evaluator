"""
Scoring system for standardizing evaluation results into traffic light indicators.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd


class TrafficLightScorer:
    """
    Converts raw metric scores into standardized traffic light indicators.

    The traffic light system provides a clear, intuitive way to interpret evaluation
    results with three levels:
    - Green: Good performance
    - Yellow: Mediocre performance that may need attention
    - Red: Poor performance that needs improvement

    Different thresholds are used for different metrics.
    """

    def __init__(
        self,
        rouge_thresholds: Tuple[float, float] = (0.4, 0.5),
        other_thresholds: Tuple[float, float] = (0.4, 0.7),
        missing_eval_threshold: float = 0.05,
    ):
        """
        Initialize the traffic light scorer.

        Args:
            rouge_thresholds: Tuple of (lower, upper) thresholds for ROUGE scores.
                Below lower is red, between lower and upper is yellow, above upper is green.
            other_thresholds: Tuple of (lower, upper) thresholds for other metrics.
                Below lower is red, between lower and upper is yellow, above upper is green.
            missing_eval_threshold: Maximum percentage of missing evaluations allowed for a green overall status.
                If more than this percentage of responses are missing evaluations, the maximum overall status is yellow.
        """
        self.rouge_thresholds = rouge_thresholds
        self.other_thresholds = other_thresholds
        self.missing_eval_threshold = missing_eval_threshold

    def score_to_status(self, score: float, metric_name: str) -> str:
        """
        Convert a raw score to a traffic light status.

        Args:
            score: Raw score (0 to 1)
            metric_name: Name of the metric

        Returns:
            Traffic light status: 'green', 'yellow', or 'red'
        """
        if metric_name == "toxicity":
            # For toxicity, the score is already inverted (1.0 for non-toxic, 0.0 for toxic)
            if score >= 1.0:
                return "green"
            return "red"

        if metric_name == "rouge":
            lower, upper = self.rouge_thresholds
        else:
            lower, upper = self.other_thresholds

        if score < lower:
            return "red"
        elif score < upper:
            return "yellow"
        else:
            return "green"

    def compute_overall_status(
        self, statuses: List[str], missing_evals: int = 0, total_evals: int = 0
    ) -> str:
        """
        Compute the overall status based on individual metric statuses.

        Args:
            statuses: List of traffic light statuses
            missing_evals: Number of missing evaluations
            total_evals: Total number of evaluations attempted

        Returns:
            Overall traffic light status: 'green', 'yellow', or 'red'
        """
        # If there are no statuses, return 'red'
        if not statuses:
            return "red"

        # Check if there are any toxicity failures (assumed to already be excluded from statuses)

        # Check if there are too many missing evaluations
        if (
            total_evals > 0
            and missing_evals / total_evals > self.missing_eval_threshold
        ):
            # If more than the threshold percentage of evaluations are missing, maximum is yellow
            if "red" in statuses:
                return "red"
            else:
                return "yellow"

        # Check for any red statuses
        if "red" in statuses:
            return "red"

        # Check for any yellow statuses
        if "yellow" in statuses:
            return "yellow"

        # If all statuses are green
        return "green"

    def score_results(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """
        Score a DataFrame of evaluation results.

        Args:
            results_df: DataFrame with columns for each metric's score

        Returns:
            DataFrame with added status columns and overall status
        """
        # Make a copy to avoid modifying the original
        df = results_df.copy()

        # Process each metric
        for col in df.columns:
            if col.endswith("_score"):
                metric_name = col.replace("_score", "")
                status_col = f"{metric_name}_status"

                # Convert scores to statuses
                df[status_col] = df[col].apply(
                    lambda x: self.score_to_status(x, metric_name)
                )

        # Handle toxicity separately as it's a boolean
        if "toxicity_is_toxic" in df.columns:
            # Convert toxicity to a status
            df["toxicity_status"] = df["toxicity_is_toxic"].apply(
                lambda x: "red" if x else "green"
            )

        # Compute overall status for each row
        df["overall_status"] = df.apply(
            lambda row: self.compute_row_status(row), axis=1
        )

        return df

    def compute_row_status(self, row: pd.Series) -> str:
        """
        Compute the status for a single row of results.

        Args:
            row: Series containing evaluation results for a single response

        Returns:
            Traffic light status: 'green', 'yellow', or 'red'
        """
        # Get all status columns
        status_cols = [col for col in row.index if col.endswith("_status")]

        # Collect statuses
        statuses = [row[col] for col in status_cols]

        # Special handling for toxicity
        if "toxicity_is_toxic" in row and row["toxicity_is_toxic"]:
            return "red"

        # Compute overall status
        return self.compute_overall_status(statuses)
