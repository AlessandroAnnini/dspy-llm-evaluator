"""
LLM Evaluator: A framework for evaluating LLM responses

This module implements an evaluation framework based on DSPy that assesses LLM responses
according to the following metrics:
- Relevancy: How well an answer aligns with the question
- Correctness: Whether the generated answer is factually accurate
- ROUGE: Text overlap with reference responses
- Toxicity: Presence of inappropriate language

Usage:
    python main.py --data path/to/evaluation_data.csv --output results.csv
"""

import os
import argparse
import pandas as pd
import dspy
from dotenv import load_dotenv

from evaluator.metrics import (
    RelevancyMetric,
    CorrectnessMetric,
    RougeMetric,
    ToxicityMetric,
)
from evaluator.scoring import TrafficLightScorer
from evaluator.pipeline import EvaluationPipeline

# Load environment variables from .env file
load_dotenv()


# Configure DSPy with appropriate LLM
def setup_dspy(api_key=None):
    """Set up DSPy with the appropriate LLM configuration."""
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "No API key provided. Set OPENAI_API_KEY environment variable in .env file or pass it as an argument."
        )

    # Get LLM provider and model name from environment variables or use defaults
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    model_name = os.environ.get("MODEL_NAME", "gpt-4")

    # Configure DSPy with the appropriate LLM provider and model name
    lm = dspy.LM(f"{llm_provider}/{model_name}", api_key=api_key)
    dspy.configure(lm=lm)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LLM responses using various metrics"
    )
    parser.add_argument(
        "--data", type=str, required=True, help="Path to the evaluation data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.environ.get("OUTPUT_DIR", "evaluation_results.csv"),
        help="Path to save evaluation results",
    )
    parser.add_argument("--api_key", type=str, help="API key for the LLM service")
    parser.add_argument(
        "--metrics",
        type=str,
        default="all",
        help="Comma-separated list of metrics to use (relevancy,correctness,rouge,toxicity) or 'all'",
    )

    args = parser.parse_args()

    # Set up DSPy
    setup_dspy(args.api_key)

    # Load evaluation data
    try:
        df = pd.read_csv(args.data)
        required_columns = ["question", "response", "reference"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Input data missing required columns: {', '.join(missing_cols)}"
            )
    except Exception as e:
        print(f"Error loading evaluation data: {e}")
        return

    # Set up metrics
    metrics = []
    if args.metrics == "all":
        metrics = [
            RelevancyMetric(),
            CorrectnessMetric(),
            RougeMetric(),
            ToxicityMetric(),
        ]
    else:
        metric_names = [m.strip().lower() for m in args.metrics.split(",")]
        if "relevancy" in metric_names:
            metrics.append(RelevancyMetric())
        if "correctness" in metric_names:
            metrics.append(CorrectnessMetric())
        if "rouge" in metric_names:
            metrics.append(RougeMetric())
        if "toxicity" in metric_names:
            metrics.append(ToxicityMetric())

    # Set up scorer with thresholds from environment variables
    relevancy_threshold = float(os.environ.get("METRICS_THRESHOLD_RELEVANCY", 0.7))
    correctness_threshold = float(os.environ.get("METRICS_THRESHOLD_CORRECTNESS", 0.7))
    rouge_threshold = float(os.environ.get("METRICS_THRESHOLD_ROUGE", 0.5))

    # Create scorer with configured thresholds
    scorer = TrafficLightScorer(
        rouge_thresholds=(rouge_threshold - 0.1, rouge_threshold),
        other_thresholds=(0.4, min(relevancy_threshold, correctness_threshold)),
    )

    # Set up evaluation pipeline
    pipeline = EvaluationPipeline(metrics=metrics, scorer=scorer)

    # Run evaluation
    results = pipeline.evaluate(df)

    # Save results
    results.to_csv(args.output, index=False)
    print(f"Evaluation complete. Results saved to {args.output}")

    # Print summary with emojis
    print("\nEvaluation Summary:")
    print("-" * 50)
    for metric in metrics:
        avg_score = results[f"{metric.name}_score"].mean()
        # Add appropriate emoji based on metric
        if metric.name == "relevancy":
            emoji = "🎯"  # Target/relevance
        elif metric.name == "correctness":
            emoji = "✅"  # Checkmark for correctness
        elif metric.name == "rouge":
            emoji = "📝"  # Document for text comparison
        elif metric.name == "toxicity":
            emoji = "🛡️"  # Shield for protection against toxicity
        else:
            emoji = "📊"  # Default chart emoji

        print(f"{emoji} {metric.name.capitalize()}: {avg_score:.2f}")

    # Reorder and add emojis to the overall status distribution
    overall_status = results["overall_status"].value_counts()
    print("\nOverall Status Distribution:")

    # Define the desired order and emojis
    status_order = ["green", "yellow", "red"]
    status_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

    # Print statuses in the specified order
    for status in status_order:
        if status in overall_status:
            count = overall_status[status]
            percentage = count / len(results) * 100
            print(f"{status_emoji[status]} {status}: {count} ({percentage:.1f}%)")
        else:
            print(f"{status_emoji[status]} {status}: 0 (0.0%)")


if __name__ == "__main__":
    main()
