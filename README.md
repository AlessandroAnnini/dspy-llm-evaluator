# LLM Evaluator with DSPy

<div align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/12657/12657344.png" alt="LLM Evaluator Metrics" width="150" height="150"/>
</div>

An evaluation framework for Large Language Model (LLM) responses using DSPy. For a comprehensive explanation of the concepts and methodology, please read our [Medium article](medium-article.md).

## Overview

This framework provides a standardized approach to evaluate LLM-generated responses across four key metrics:

1. **Relevancy:** How well the answer aligns with the question
2. **Correctness:** Factual accuracy compared to ground truth
3. **ROUGE:** Text overlap with reference responses
4. **Toxicity:** Detection of inappropriate content

Results are standardized into a traffic light system (🟢 Green, 🟡 Yellow, 🔴 Red) for intuitive interpretation. For detailed explanations of these metrics and the evaluation methodology, refer to our [Medium article](medium-article.md).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dspy-llm-evaluator.git
cd dspy-llm-evaluator

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy the provided `.env.example` file to create your own `.env` file:

```bash
cp .env.example .env
```

Key environment variables:

| Variable                        | Description                                   | Default                |
| ------------------------------- | --------------------------------------------- | ---------------------- |
| `OPENAI_API_KEY`                | Your OpenAI API key                           | None (Required)        |
| `LLM_PROVIDER`                  | The LLM provider to use                       | openai                 |
| `MODEL_NAME`                    | The LLM model to use                          | gpt-4o                 |
| `METRICS_THRESHOLD_RELEVANCY`   | Threshold for relevancy metric                | 0.7                    |
| `METRICS_THRESHOLD_CORRECTNESS` | Threshold for correctness metric              | 0.7                    |
| `METRICS_THRESHOLD_ROUGE`       | Threshold for ROUGE metric                    | 0.5                    |
| `OUTPUT_DIR`                    | Directory or file path for evaluation results | evaluation_results.csv |
| `LOG_LEVEL`                     | Logging level                                 | INFO                   |

For supported LLM providers, see [DSPy docs](https://dspy.ai/#__tabbed_1_1).

## Usage

### Basic Usage

```bash
python main.py --data path/to/evaluation_data.csv --output results.csv
```

### Command Line Arguments

- `--data`: Path to the evaluation data CSV (required)
- `--output`: Path to save evaluation results (default: evaluation_results.csv)
- `--api_key`: API key for the LLM service (can also be set via environment variable)
- `--metrics`: Comma-separated list of metrics to use (options: relevancy,correctness,rouge,toxicity or 'all')

### Input Data Format

The input CSV should contain:

- `question`: The question or prompt given to the LLM
- `response`: The LLM's response to evaluate
- `reference`: The reference or ground truth answer

Example:

```csv
question,response,reference
"Who won the FIFA World Cup in 2014?","Germany won the FIFA World Cup in 2014 by defeating Argentina 1-0 in the final.","Germany won the FIFA World Cup in 2014 by defeating Argentina 1-0 in the final."
```

### Output Example

```
Evaluating responses: 100%|███████████████████████████████████████████████| 11/11 [00:00<00:00, 89.32it/s]
Evaluation complete. Results saved to sample_result.csv

Evaluation Summary:
--------------------------------------------------
🎯 Relevancy: 0.55
✅ Correctness: 0.53
📝 Rouge: 0.41
🛡 Toxicity: 0.91

Overall Status Distribution:
🟢 green: 2 (18.2%)
🟡 yellow: 2 (18.2%)
🔴 red: 7 (63.6%)
```

## Utility Script

The project includes a utility script for post-processing evaluation results:

```bash
python scripts/llm_eval_utils.py <command> [arguments]
```

Available commands:

- `check-quality`: Validates if results meet quality thresholds
- `generate-trends`: Creates trend reports from historical data
- `compare-models`: Compares results from different models
- `generate-report`: Generates HTML reports
- `check-deployment`: Checks if results meet deployment criteria

Example:

```bash
# Generate HTML report
python scripts/llm_eval_utils.py generate-report --results evaluation_results.csv --output report.html
```

## Integration with CI/CD

This evaluator can be integrated into CI/CD pipelines to ensure consistent performance of LLM assistants. See the [GitLab Integration Guide](docs/gitlab_integration.md) for details on:

- Setting up GitLab CI/CD pipelines for automated evaluations
- Configuring quality thresholds for pipeline success/failure
- Tracking evaluation metrics over time
- Comparing different model versions
- Generating reports and visualizations

## Architecture

The application follows a modular design for extensibility and maintainability:

### Core Components

1. **Metrics System**

   - Abstract `Metric` and `DSPyMetric` base classes
   - Individual implementations for each metric type

2. **DSPy Integration**

   - Leverages DSPy for consistent LLM-based evaluation
   - Custom DSPy signatures and programs for evaluation

3. **Scoring System**

   - `TrafficLightScorer` standardizes scores (green/yellow/red)
   - Configurable thresholds for evaluation strictness

4. **Evaluation Pipeline**
   - Orchestrates end-to-end evaluation process
   - Handles parallel metric application and aggregation

### Extensibility

To add new metrics:

1. Create a new class inheriting from `Metric` or `DSPyMetric`
2. Implement the required `evaluate()` method
3. Register the new metric in `__init__.py`

For more details on the conceptual framework and methodology, please refer to our [Medium article](medium-article.md) or the original ["LLM Evaluator: what AI Scientist must know"](https://medium.com/@mattiadeleo33/llm-evaluator-what-ai-scientist-must-know-ca774d381ffe) article.
