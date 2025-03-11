# LLM Evaluator with DSPy

An evaluation framework for Large Language Model (LLM) responses using DSPy, based on the principles described in the ["LLM Evaluator: what AI Scientist must know"](https://medium.com/@mattiadeleo33/llm-evaluator-what-ai-scientist-must-know-ca774d381ffe) article.

## Overview

Evaluating LLMs presents unique challenges compared to traditional ML models. While classical ML can be assessed through well-defined metrics like accuracy or F1-score, LLM evaluation requires a more nuanced approach that considers qualitative aspects of responses.

This framework evaluates LLM-generated responses across four key metrics:

1. **Relevancy:** Measures how well an answer aligns with the question. A highly relevant answer directly addresses the user's query without unnecessary information or deviations. This can be assessed using semantic similarity between question and answer.
2. **Correctness:** Evaluates whether the generated answer is factually accurate when compared to a known ground truth. This ensures responses don't contain incorrect or misleading information.
3. **ROUGE:** (Recall-Oriented Understudy for Gisting Evaluation) Measures text overlap with reference responses. This set of metrics evaluates how much a generated response contains the same information as a reference answer.
4. **Toxicity:** Detects the presence of inappropriate, offensive, discriminatory, or violent language. This metric is essential for ensuring user safety and maintaining ethical AI interactions.

Results are standardized into a traffic light system:

- 🟢 **Green**: Good performance (scores ≥ 0.7, ROUGE > 0.5)
- 🟡 **Yellow**: Mediocre performance that needs attention (scores 0.4-0.7, ROUGE 0.4-0.5)
- 🔴 **Red**: Poor performance that needs improvement (scores < 0.4, ROUGE < 0.4)

For toxicity, which is a binary indicator (present/not present), any detection immediately flags the response as problematic.

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

The project uses python-dotenv to manage environment variables. Copy the provided `.env.example` file to create your own `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your API keys and configure the evaluation settings.

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

Supported LLM providers:

see [DSPy docs](https://dspy.ai/#__tabbed_1_1)

You can also test that your environment variables are loaded correctly:

```bash
python test_dotenv.py
```

## Usage

### Basic Usage

```bash
python main.py --data path/to/evaluation_data.csv --output results.csv
```

### Command Line Arguments

- `--data`: Path to the evaluation data CSV (required)
- `--output`: Path to save evaluation results (default: evaluation_results.csv)
- `--api_key`: API key for the LLM service (can also be set via OPENAI_API_KEY environment variable)
- `--metrics`: Comma-separated list of metrics to use (options: relevancy,correctness,rouge,toxicity or 'all')

### Input Data Format

The input CSV should contain the following columns:

- `question`: The question or prompt given to the LLM
- `response`: The LLM's response to evaluate
- `reference`: The reference or ground truth answer

Example:

```csv
question,response,reference
"Who won the FIFA World Cup in 2014?","Germany won the FIFA World Cup in 2014 by defeating Argentina 1-0 in the final.","Germany won the FIFA World Cup in 2014 by defeating Argentina 1-0 in the final."
```

### Output Format

The output CSV includes the original data plus:

- Metric scores (0-1) for each evaluation metric
- Traffic light status for each metric (green, yellow, red)
- Overall status based on all metrics

## Integration with CI/CD

This evaluator can be integrated into a CI/CD pipeline to ensure consistent performance of LLM-powered assistants. See the [GitLab Integration Guide](docs/gitlab_integration.md) for details.

## Architecture

The application is structured following modular design principles to ensure extensibility and maintainability:

### Core Components

1. **Metrics System**

   - `evaluator/metrics/base.py`: Defines the abstract `Metric` and `DSPyMetric` base classes that all metrics must implement
   - Individual metric implementations follow a consistent pattern:
     - `RelevancyMetric`: Evaluates how well a response addresses the original question
     - `CorrectnessMetric`: Assesses factual accuracy of responses against references
     - `RougeMetric`: Computes text overlap between responses and references
     - `ToxicityMetric`: Detects inappropriate or harmful content in responses

2. **DSPy Integration**

   - Each metric leverages DSPy for consistent LLM-based evaluation
   - Metrics define custom DSPy signatures and programs via the `build_dspy_program()` method
   - This approach ensures consistent prompting and interpretation of LLM outputs for evaluation

3. **Scoring System**

   - The `TrafficLightScorer` class standardizes raw metric scores into a traffic light system (green/yellow/red)
   - Configurable thresholds allow customization of evaluation strictness

4. **Evaluation Pipeline**
   - `EvaluationPipeline` orchestrates the end-to-end evaluation process
   - Handles parallel application of metrics to each test case
   - Aggregates individual metric results into overall evaluation scores

### Control Flow

The application follows this flow:

1. Parse command-line arguments and environment variables for configuration
2. Set up the DSPy framework with appropriate LLM provider and model
3. Load and validate evaluation data from the input CSV
4. Initialize requested metrics with appropriate thresholds
5. Execute the evaluation pipeline on all test cases
6. Generate and save detailed results in CSV format
7. Display summary statistics with appropriate visualizations

### Extensibility

The architecture makes it straightforward to add new metrics by:

1. Creating a new metric class that inherits from `Metric` or `DSPyMetric`
2. Implementing the required `evaluate()` method and any DSPy-specific components
3. Registering the new metric in `__init__.py` and adding it to the metric selection in `main.py`

This modular design allows the framework to evolve with advances in LLM evaluation techniques while maintaining a consistent interface.
