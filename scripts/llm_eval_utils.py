#!/usr/bin/env python3
"""
LLM Evaluator Utility Script

A unified utility script for processing and analyzing LLM evaluation results.
This script provides multiple subcommands to:
- Check evaluation quality thresholds
- Generate trend reports and visualizations
- Compare multiple model evaluations
- Generate HTML reports

Usage:
    python llm_eval_utils.py check-quality --results results.csv --min-green 70
    python llm_eval_utils.py generate-trends --history-dir eval_history --output trends.png
    python llm_eval_utils.py compare-models --results1 model1.csv --results2 model2.csv --output comparison.html
    python llm_eval_utils.py generate-report --results results.csv --output report.html
"""

import argparse
import sys
import os
import pandas as pd
import json
from datetime import datetime

# Configure matplotlib to use non-interactive Agg backend to prevent hanging
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any, Union


# ------------------- Utility Functions -------------------


def load_results(file_path: str) -> pd.DataFrame:
    """Load and validate evaluation results from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ["overall_status"]

        # Check if required columns exist
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        return df
    except Exception as e:
        print(f"Error loading results file {file_path}: {e}")
        sys.exit(1)


def get_status_counts(df: pd.DataFrame) -> Tuple[Dict[str, int], int, float]:
    """Calculate status distribution and green percentage."""
    status_counts = df["overall_status"].value_counts().to_dict()
    total = len(df)
    green_count = status_counts.get("green", 0)
    green_percentage = (green_count / total) * 100 if total > 0 else 0

    return status_counts, total, green_percentage


def get_metric_scores(df: pd.DataFrame) -> Dict[str, float]:
    """Extract and calculate average metric scores."""
    metric_cols = [col for col in df.columns if col.endswith("_score")]
    return {col: df[col].mean() for col in metric_cols}


def create_metrics_report(
    file_path: str,
    avg_scores: Dict[str, float],
    status_counts: Dict[str, int],
    total: int,
) -> None:
    """Create a metrics report file for GitLab CI."""
    with open(file_path, "w") as f:
        # Write metric scores
        for metric, score in avg_scores.items():
            clean_name = metric.replace("_score", "")
            f.write(f"{clean_name}_score {score:.4f}\n")

        # Write status percentages
        for status in ["green", "yellow", "red"]:
            percentage = (
                (status_counts.get(status, 0) / total) * 100 if total > 0 else 0
            )
            f.write(f"{status}_percentage {percentage:.2f}\n")


# ------------------- Command Functions -------------------


def better_class(val1: float, val2: float) -> str:
    """Return CSS class name based on whether the first value is better than the second."""
    return "better" if val1 > val2 else ""


def check_quality(args: argparse.Namespace) -> None:
    """Check if evaluation results meet quality thresholds."""
    df = load_results(args.results)
    status_counts, total, green_percentage = get_status_counts(df)
    avg_scores = get_metric_scores(df)

    # Create metrics report
    create_metrics_report("metrics_report.txt", avg_scores, status_counts, total)

    # Print summary
    print(f"Evaluation Summary:")
    print(f"Total evaluations: {total}")
    print(
        f"Green evaluations: {status_counts.get('green', 0)} ({green_percentage:.2f}%)"
    )
    print(f"Minimum required: {args.min_green}%")

    # Check if quality threshold is met
    if green_percentage < args.min_green:
        print(
            f"❌ Quality check failed: {green_percentage:.2f}% green evaluations is below "
            f"the minimum threshold of {args.min_green}%"
        )
        sys.exit(1)
    else:
        print(
            f"✅ Quality check passed: {green_percentage:.2f}% green evaluations meets or "
            f"exceeds the threshold of {args.min_green}%"
        )
        sys.exit(0)


def generate_trends(args: argparse.Namespace) -> None:
    """Generate trend reports and visualizations from historical evaluation data."""
    # Ensure history directory exists
    if not os.path.exists(args.history_dir):
        print(f"Error: History directory {args.history_dir} does not exist")
        sys.exit(1)

    # Find all CSV files in the history directory
    csv_files = [f for f in os.listdir(args.history_dir) if f.endswith(".csv")]
    if not csv_files:
        print(f"No CSV files found in {args.history_dir}")
        sys.exit(1)

    # Process each file
    trend_data = []
    for file in csv_files:
        try:
            # Try to extract date from filename (assuming format YYYY-MM-DD_HH-MM-SS.csv)
            date_str = file.split(".")[0]
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            except:
                # Fall back to file modification time
                date = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(args.history_dir, file))
                )

            # Load and analyze file
            df = pd.read_csv(os.path.join(args.history_dir, file))
            status_counts, total, green_percentage = get_status_counts(df)
            avg_scores = get_metric_scores(df)

            # Add to trend data
            entry = {"date": date, "green_percentage": green_percentage}
            entry.update({k.replace("_score", ""): v for k, v in avg_scores.items()})
            trend_data.append(entry)

        except Exception as e:
            print(f"Warning: Could not process {file}: {e}")

    if not trend_data:
        print("No valid data found for trend analysis")
        sys.exit(1)

    # Convert to DataFrame for plotting
    trend_df = pd.DataFrame(trend_data)
    trend_df = trend_df.sort_values("date")

    # Generate plots
    plt.figure(figsize=(12, 8))

    # Plot 1: Green percentage over time
    plt.subplot(2, 1, 1)
    plt.plot(trend_df["date"], trend_df["green_percentage"], marker="o", linewidth=2)
    plt.title("Green Evaluation Percentage Over Time")
    plt.ylabel("Percentage")
    plt.grid(True)

    # Plot 2: Metric scores over time
    plt.subplot(2, 1, 2)
    metrics = [
        col for col in trend_df.columns if col not in ["date", "green_percentage"]
    ]
    for metric in metrics:
        plt.plot(trend_df["date"], trend_df[metric], marker="o", label=metric)
    plt.title("Metric Scores Over Time")
    plt.ylabel("Score")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(args.output)
    print(f"Trend visualization saved to {args.output}")

    # Close the figure to prevent the script from hanging
    plt.close()

    # Also save trend data as CSV
    csv_output = args.output.rsplit(".", 1)[0] + "_data.csv"
    trend_df.to_csv(csv_output, index=False)
    print(f"Trend data saved to {csv_output}")


def compare_models(args: argparse.Namespace) -> None:
    """Compare evaluation results from two different models or test runs."""
    # Load results
    df1 = load_results(args.results1)
    df2 = load_results(args.results2)

    # Get model names (from filenames if not provided)
    model1_name = args.model1 or os.path.basename(args.results1)  # .split("_")[0]
    model2_name = args.model2 or os.path.basename(args.results2)  # .split("_")[0]

    # Calculate metrics for both models
    _, total1, green_percentage1 = get_status_counts(df1)
    _, total2, green_percentage2 = get_status_counts(df2)
    avg_scores1 = get_metric_scores(df1)
    avg_scores2 = get_metric_scores(df2)

    # Prepare comparison data
    comparison_data = {
        "model1": {
            "name": model1_name,
            "total_evaluations": total1,
            "green_percentage": green_percentage1,
            "metrics": {k.replace("_score", ""): v for k, v in avg_scores1.items()},
        },
        "model2": {
            "name": model2_name,
            "total_evaluations": total2,
            "green_percentage": green_percentage2,
            "metrics": {k.replace("_score", ""): v for k, v in avg_scores2.items()},
        },
    }

    # Generate comparison visualization
    plt.figure(figsize=(12, 10))

    # Plot 1: Green percentage comparison
    plt.subplot(2, 1, 1)
    models = [model1_name, model2_name]
    green_percentages = [green_percentage1, green_percentage2]
    plt.bar(models, green_percentages, color=["#4CAF50", "#2196F3"])
    plt.title("Green Evaluation Percentage Comparison")
    plt.ylabel("Percentage")
    plt.ylim(0, 100)
    for i, v in enumerate(green_percentages):
        plt.text(i, v + 2, f"{v:.1f}%", ha="center")

    # Plot 2: Metric comparison
    plt.subplot(2, 1, 2)
    metrics1 = comparison_data["model1"]["metrics"]
    metrics2 = comparison_data["model2"]["metrics"]

    # Get common metrics
    all_metrics = sorted(set(list(metrics1.keys()) + list(metrics2.keys())))

    # Set up positions for bars
    x = range(len(all_metrics))
    width = 0.35

    # Create bars
    scores1 = [metrics1.get(m, 0) for m in all_metrics]
    scores2 = [metrics2.get(m, 0) for m in all_metrics]

    plt.bar(
        [p - width / 2 for p in x], scores1, width, label=model1_name, color="#4CAF50"
    )
    plt.bar(
        [p + width / 2 for p in x], scores2, width, label=model2_name, color="#2196F3"
    )

    plt.title("Metric Scores Comparison")
    plt.ylabel("Score")
    plt.xticks(x, all_metrics, rotation=45)
    plt.legend()
    plt.ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(args.output.rsplit(".", 1)[0] + ".png")

    # Close the figure to prevent the script from hanging
    plt.close()

    # Generate HTML report
    html_output = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Comparison: {model1_name} vs {model2_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .comparison-table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            .comparison-table th, .comparison-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .comparison-table th {{ background-color: #f2f2f2; }}
            .comparison-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .better {{ color: green; font-weight: bold; }}
            h1, h2 {{ color: #333; }}
            .container {{ margin-top: 30px; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h1>Model Comparison: {model1_name} vs {model2_name}</h1>

        <div class="container">
            <h2>Overall Performance</h2>
            <table class="comparison-table">
                <tr>
                    <th>Metric</th>
                    <th>{model1_name}</th>
                    <th>{model2_name}</th>
                    <th>Difference</th>
                </tr>
                <tr>
                    <td>Total Evaluations</td>
                    <td>{total1}</td>
                    <td>{total2}</td>
                    <td>{total2 - total1}</td>
                </tr>
                <tr>
                    <td>Green Percentage</td>
                    <td>{green_percentage1:.2f}%</td>
                    <td>{green_percentage2:.2f}%</td>
                    <td class="{better_class(green_percentage2, green_percentage1)}">
                        {green_percentage2 - green_percentage1:.2f}%
                    </td>
                </tr>
            </table>
        </div>

        <div class="container">
            <h2>Metric Scores</h2>
            <table class="comparison-table">
                <tr>
                    <th>Metric</th>
                    <th>{model1_name}</th>
                    <th>{model2_name}</th>
                    <th>Difference</th>
                </tr>
    """

    for metric in all_metrics:
        score1 = metrics1.get(metric, 0)
        score2 = metrics2.get(metric, 0)
        diff = score2 - score1
        diff_class = "better" if diff > 0 else ""

        html_output += f"""
                <tr>
                    <td>{metric}</td>
                    <td>{score1:.4f}</td>
                    <td>{score2:.4f}</td>
                    <td class="{diff_class}">{diff:.4f}</td>
                </tr>
        """

    html_output += f"""
            </table>
        </div>

        <div class="container">
            <h2>Visualizations</h2>
            <img src="{os.path.basename(args.output).rsplit('.', 1)[0] + '.png'}" alt="Comparison Charts">
        </div>
    </body>
    </html>
    """

    with open(args.output, "w") as f:
        f.write(html_output)

    print(f"Comparison report saved to {args.output}")
    print(f"Comparison visualization saved to {args.output.rsplit('.', 1)[0] + '.png'}")


def generate_report(args: argparse.Namespace) -> None:
    """Generate a standalone HTML report from evaluation results."""
    df = load_results(args.results)
    status_counts, total, green_percentage = get_status_counts(df)
    avg_scores = get_metric_scores(df)

    # Create a summary dictionary
    summary = {
        "total_evaluations": total,
        "status_distribution": status_counts,
        "status_percentages": {
            status: (count / total * 100) for status, count in status_counts.items()
        },
        "average_scores": avg_scores,
    }

    # Calculate percentages for status distribution
    green_percent = status_counts.get("green", 0) / total * 100 if total > 0 else 0
    yellow_percent = status_counts.get("yellow", 0) / total * 100 if total > 0 else 0
    red_percent = status_counts.get("red", 0) / total * 100 if total > 0 else 0

    # Close any existing matplotlib figures to avoid resource leaks
    plt.close("all")

    # Create HTML report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LLM Evaluation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1, h2, h3 {{ color: #333; }}
            .summary-box {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
            }}
            .metric {{
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }}
            .metric-name {{
                width: 120px;
                font-weight: bold;
            }}
            .metric-value {{
                font-size: 18px;
                margin-right: 10px;
            }}
            .metric-bar {{
                height: 20px;
                background-color: #4CAF50;
                border-radius: 3px;
            }}
            .status-green {{ color: #4CAF50; }}
            .status-yellow {{ color: #FFC107; }}
            .status-red {{ color: #F44336; }}
            .chart {{ margin: 30px 0; max-width: 100%; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr {{ background-color: #f9f9f9; }}
            .green {{ background-color: rgba(76, 175, 80, 0.2); }}
            .yellow {{ background-color: rgba(255, 193, 7, 0.2); }}
            .red {{ background-color: rgba(244, 67, 54, 0.2); }}

            /* Vertical bar chart styles */
            .vertical-chart {{
                display: flex;
                justify-content: space-around;
                align-items: flex-end;
                height: 250px;
                margin: 30px 0;
                padding: 0 20px;
                border: 1px solid #ddd;
                background-color: #fff;
                position: relative;
            }}
            .vertical-chart::after {{
                content: '';
                position: absolute;
                left: 0;
                right: 0;
                bottom: 0;
                height: 1px;
                background-color: #333;
            }}
            .vertical-chart::before {{
                content: 'Score';
                position: absolute;
                left: -40px;
                top: 125px;
                transform: rotate(-90deg);
                font-size: 14px;
                font-weight: bold;
            }}
            .vertical-bar-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 80px;
                height: 100%;
                position: relative;
            }}
            .vertical-bar {{
                width: 50px;
                background-color: #2196F3;
                border-radius: 3px 3px 0 0;
                position: absolute;
                bottom: 0;
            }}
            .vertical-bar-label {{
                position: absolute;
                bottom: -30px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                width: 100%;
            }}
            .vertical-bar-value {{
                position: absolute;
                top: -20px;
                text-align: center;
                font-size: 12px;
                width: 100%;
                font-weight: bold;
            }}
            .y-axis-line {{
                position: absolute;
                left: 0;
                right: 0;
                height: 1px;
                background-color: rgba(0,0,0,0.1);
            }}
            .y-axis-label {{
                position: absolute;
                left: 5px;
                font-size: 10px;
                transform: translateY(-50%);
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h1>LLM Evaluation Report</h1>
        <p>Generated on: {timestamp}</p>

        <div class="summary-box">
            <h2>Summary</h2>
            <div class="metric">
                <span class="metric-name">Total evaluations:</span>
                <span class="metric-value">{total}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Green results:</span>
                <span class="metric-value status-green">{status_counts.get("green", 0)} ({green_percent:.1f}%)</span>
                <div class="metric-bar" style="width: {green_percent}%;"></div>
            </div>
            <div class="metric">
                <span class="metric-name">Yellow results:</span>
                <span class="metric-value status-yellow">{status_counts.get("yellow", 0)} ({yellow_percent:.1f}%)</span>
                <div class="metric-bar" style="background-color: #FFC107; width: {yellow_percent}%;"></div>
            </div>
            <div class="metric">
                <span class="metric-name">Red results:</span>
                <span class="metric-value status-red">{status_counts.get("red", 0)} ({red_percent:.1f}%)</span>
                <div class="metric-bar" style="background-color: #F44336; width: {red_percent}%;"></div>
            </div>
        </div>

        <h2>Metric Averages</h2>
        <div style="position: relative; margin-top: 30px; margin-bottom: 40px;">
            <h3 style="text-align: center; margin-bottom: 5px;">Average Metric Scores</h3>
            <div class="vertical-chart">
                <!-- Y-axis lines and labels -->
                <div class="y-axis-line" style="bottom: 0%; left: 0; width: 100%;"></div>
                <div class="y-axis-line" style="bottom: 20%; left: 0; width: 100%;">
                    <span class="y-axis-label">0.2</span>
                </div>
                <div class="y-axis-line" style="bottom: 40%; left: 0; width: 100%;">
                    <span class="y-axis-label">0.4</span>
                </div>
                <div class="y-axis-line" style="bottom: 60%; left: 0; width: 100%;">
                    <span class="y-axis-label">0.6</span>
                </div>
                <div class="y-axis-line" style="bottom: 80%; left: 0; width: 100%;">
                    <span class="y-axis-label">0.8</span>
                </div>
                <div class="y-axis-line" style="bottom: 100%; left: 0; width: 100%;">
                    <span class="y-axis-label">1.0</span>
                </div>
    """

    # Add vertical bars for each metric
    for metric, score in avg_scores.items():
        clean_name = metric.replace("_score", "").capitalize()
        height_percentage = score * 100
        html += f"""
                <div class="vertical-bar-container">
                    <div class="vertical-bar" style="height: {height_percentage}%;">
                        <span class="vertical-bar-value">{score:.2f}</span>
                    </div>
                    <span class="vertical-bar-label">{clean_name}</span>
                </div>
        """

    html += """
            </div>
        </div>

        <h2>Evaluation Details</h2>
        <table>
            <tr>
                <th>Question</th>
                <th>Response</th>
                <th>Reference</th>
                <th>Status</th>
    """

    # Add metric columns to table header
    for metric in [k.replace("_score", "") for k in avg_scores.keys()]:
        html += f"<th>{metric.capitalize()}</th>\n"

    html += "</tr>\n"

    # Add rows for each evaluation
    for i, row in df.head(
        100
    ).iterrows():  # Limit to first 100 rows to avoid huge HTML files
        status_class = row["overall_status"]

        html += f"""
            <tr class="{status_class}">
                <td>{row.get("question", "")[:100] + "..." if len(str(row.get("question", ""))) > 100 else row.get("question", "")}</td>
                <td>{row.get("response", "")[:100] + "..." if len(str(row.get("response", ""))) > 100 else row.get("response", "")}</td>
                <td>{row.get("reference", "")[:100] + "..." if len(str(row.get("reference", ""))) > 100 else row.get("reference", "")}</td>
                <td class="status-{status_class}">{row["overall_status"].capitalize()}</td>
        """

        # Add metric scores to row
        for metric in avg_scores.keys():
            if metric in row:
                html += f"<td>{row[metric]:.4f}</td>\n"
            else:
                html += "<td>N/A</td>\n"

        html += "</tr>\n"

    if len(df) > 100:
        html += f"""
            <tr>
                <td colspan="{4 + len(avg_scores)}" style="text-align: center;">
                    <i>Showing 100 of {len(df)} results. See CSV file for full data.</i>
                </td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    with open(args.output, "w") as f:
        f.write(html)

    print(f"HTML report generated at {args.output}")


def check_deployment(args: argparse.Namespace) -> None:
    """Check if evaluation results meet deployment criteria."""
    df = load_results(args.results)
    _, _, green_percentage = get_status_counts(df)

    if green_percentage >= args.threshold:
        print(
            f"✅ Deployment check passed: {green_percentage:.2f}% green evaluations meets "
            f"or exceeds the threshold of {args.threshold}%"
        )
        sys.exit(0)
    else:
        print(
            f"❌ Deployment check failed: {green_percentage:.2f}% green evaluations is below "
            f"the threshold of {args.threshold}%"
        )
        sys.exit(1)


# ------------------- Main Function -------------------


def main():
    parser = argparse.ArgumentParser(
        description="LLM Evaluator Utility Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Check quality command
    check_quality_parser = subparsers.add_parser(
        "check-quality", help="Check if evaluation results meet quality thresholds"
    )
    check_quality_parser.add_argument(
        "--results", required=True, help="Path to evaluation results CSV"
    )
    check_quality_parser.add_argument(
        "--min-green",
        type=float,
        default=70.0,
        help="Minimum percentage of green evaluations required",
    )

    # Generate trends command
    trend_parser = subparsers.add_parser(
        "generate-trends", help="Generate trend reports from historical evaluation data"
    )
    trend_parser.add_argument(
        "--history-dir",
        required=True,
        help="Directory containing historical evaluation CSVs",
    )
    trend_parser.add_argument(
        "--output", default="trends.png", help="Output file for trend visualization"
    )

    # Compare models command
    compare_parser = subparsers.add_parser(
        "compare-models", help="Compare evaluation results from two different models"
    )
    compare_parser.add_argument(
        "--results1", required=True, help="Path to first model's evaluation results CSV"
    )
    compare_parser.add_argument(
        "--results2",
        required=True,
        help="Path to second model's evaluation results CSV",
    )
    compare_parser.add_argument(
        "--model1", help="Name for the first model (defaults to filename)"
    )
    compare_parser.add_argument(
        "--model2", help="Name for the second model (defaults to filename)"
    )
    compare_parser.add_argument(
        "--output",
        default="model_comparison.html",
        help="Output file for comparison report",
    )

    # Generate report command
    report_parser = subparsers.add_parser(
        "generate-report", help="Generate HTML report from evaluation results"
    )
    report_parser.add_argument(
        "--results", required=True, help="Path to evaluation results CSV"
    )
    report_parser.add_argument(
        "--output", default="evaluation_report.html", help="Output file for HTML report"
    )

    # Check deployment command
    deploy_parser = subparsers.add_parser(
        "check-deployment", help="Check if evaluation results meet deployment criteria"
    )
    deploy_parser.add_argument(
        "--results", required=True, help="Path to evaluation results CSV"
    )
    deploy_parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Threshold percentage of green evaluations required for deployment",
    )

    args = parser.parse_args()

    # Execute the appropriate command
    if args.command == "check-quality":
        check_quality(args)
    elif args.command == "generate-trends":
        generate_trends(args)
    elif args.command == "compare-models":
        compare_models(args)
    elif args.command == "generate-report":
        generate_report(args)
    elif args.command == "check-deployment":
        check_deployment(args)
    else:
        parser.print_help()
        sys.exit(1)

    # Final cleanup: make sure all matplotlib figures are closed
    plt.close("all")


if __name__ == "__main__":
    main()
