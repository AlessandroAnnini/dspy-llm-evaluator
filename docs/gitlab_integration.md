# GitLab CI/CD Integration Guide

This guide explains how to integrate the LLM Evaluator with your GitLab CI/CD pipeline to automatically evaluate LLM responses as part of your development workflow.

## Overview

Integrating the LLM Evaluator into your GitLab CI/CD pipeline enables you to:

- Automatically evaluate LLM responses against a test dataset
- Ensure quality standards are maintained across code changes
- Track evaluation metrics over time
- Fail builds when responses don't meet quality thresholds

## Prerequisites

Before setting up the integration, ensure you have:

- A GitLab repository with CI/CD enabled
- Docker runner configured for your GitLab project
- API key(s) for your LLM provider(s)
- A test dataset in CSV format with the required columns:
  - `question`: The question or prompt given to the LLM
  - `response`: The LLM's response to evaluate
  - `reference`: The reference or ground truth answer

## Setup Instructions

### 1. Add API Keys as CI/CD Variables

Store your API keys securely in GitLab CI/CD variables:

1. Go to your project's **Settings > CI/CD > Variables**
2. Add a new variable named `OPENAI_API_KEY` (or another provider key)
3. Set the value to your API key
4. Check "Mask variable" to hide it in job logs
5. Optionally, check "Protect variable" to restrict it to protected branches

### 2. Create a `.gitlab-ci.yml` File

Add a `.gitlab-ci.yml` file to your repository with the following configuration:

```yaml
stages:
  - test
  - evaluate

variables:
  MODEL_NAME: 'gpt-4o' # Default model, can be overridden
  LLM_PROVIDER: 'openai' # Default provider, can be overridden
  METRICS_THRESHOLD_RELEVANCY: '0.7'
  METRICS_THRESHOLD_CORRECTNESS: '0.7'
  METRICS_THRESHOLD_ROUGE: '0.5'
  EVALUATION_DATASET: 'test_data/evaluation_data.csv'
  METRICS: 'all' # Use all available metrics
  MINIMUM_GREEN_PERCENTAGE: '70' # Fail if less than 70% of evaluations are green

llm-evaluation:
  stage: evaluate
  image: python:3.10-slim
  script:
    - pip install -r requirements.txt
    - python main.py --data $EVALUATION_DATASET --output evaluation_results.csv --metrics $METRICS
    - python scripts/llm_eval_utils.py check-quality --results evaluation_results.csv --min-green $MINIMUM_GREEN_PERCENTAGE
  artifacts:
    paths:
      - evaluation_results.csv
      - metrics_report.txt
    reports:
      metrics: metrics_report.txt
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

### 3. Utility Script

We've created a comprehensive utility script at `scripts/llm_eval_utils.py` that handles all operations needed for CI/CD integration. This script provides multiple subcommands that replace the need for separate scripts:

```bash
python scripts/llm_eval_utils.py <command> [arguments]
```

Available commands:

- `check-quality`: Validates if evaluation results meet quality thresholds
- `generate-trends`: Creates trend reports from historical evaluation data
- `compare-models`: Compares results from two different models or runs
- `generate-report`: Generates HTML reports from evaluation results
- `check-deployment`: Checks if results meet deployment criteria

Example usage in CI/CD pipelines:

```yaml
# Quality check (used in the main pipeline)
- python scripts/llm_eval_utils.py check-quality --results evaluation_results.csv --min-green 70

# Generate trend report
- python scripts/llm_eval_utils.py generate-trends --history-dir evaluation_history --output trends.png

# Compare two models
- python scripts/llm_eval_utils.py compare-models --results1 model1_results.csv --results2 model2_results.csv --output comparison.html

# Generate HTML report
- python scripts/llm_eval_utils.py generate-report --results evaluation_results.csv --output report.html

# Check if ready for deployment
- python scripts/llm_eval_utils.py check-deployment --results evaluation_results.csv --threshold 85
```

For full details of available options, run:

```bash
python scripts/llm_eval_utils.py -h
```

### 4. Detailed Command Explanations

Each utility script command serves a specific purpose in the LLM evaluation pipeline:

#### `check-quality`

**Example:** `python scripts/llm_eval_utils.py check-quality --results evaluation_results.csv --min-green 70`

**What it does:**

- Analyzes evaluation results to determine if they meet specified quality thresholds
- Calculates the percentage of "green" (passing) evaluations
- Compares this percentage against a minimum acceptable threshold
- Returns a success or failure status code that can be used to pass or fail CI jobs

**Why it's important:**

- Provides an automated quality gate that prevents low-quality LLM responses from being deployed
- Creates a standardized, objective measure of quality
- Enables teams to enforce quality standards across all code changes
- Catches performance degradation before it reaches production

#### `generate-trends`

**Example:** `python scripts/llm_eval_utils.py generate-trends --history-dir evaluation_history --output trends.png`

**What it does:**

- Analyzes historical evaluation data stored in a directory
- Creates visualizations showing how evaluation metrics have changed over time
- Generates both visual charts and CSV data files with trend information
- Tracks metrics like green percentage and individual score types over time

**Why it's important:**

- Provides longitudinal data to identify gradual improvements or regressions
- Helps teams understand the impact of changes to models or prompts
- Creates visual artifacts that can be reviewed by non-technical stakeholders
- Supports data-driven decision making about LLM quality

#### `compare-models`

**Example:** `python scripts/llm_eval_utils.py compare-models --results1 model1_results.csv --results2 model2_results.csv --output comparison.html`

**What it does:**

- Compares evaluation results from two different models or test runs
- Creates side-by-side comparisons of key metrics and scores
- Generates visualizations highlighting the differences
- Produces an HTML report with detailed comparison information

**Why it's important:**

- Facilitates A/B testing between different models or prompt strategies
- Provides objective data to guide model selection decisions
- Helps quantify improvements when upgrading to newer model versions
- Makes differences between approaches clear and actionable

#### `generate-report`

**Example:** `python scripts/llm_eval_utils.py generate-report --results evaluation_results.csv --output report.html`

**What it does:**

- Creates a comprehensive, human-readable HTML report from evaluation results
- Visualizes metric distributions and evaluation status
- Includes detailed tables with individual evaluation results
- Presents information in a structured, accessible format

**Why it's important:**

- Transforms raw evaluation data into an easily digestible format
- Makes evaluation results accessible to non-technical team members
- Provides artifacts that can be attached to merge requests for review
- Facilitates deeper analysis of specific evaluation cases

#### `check-deployment`

**Example:** `python scripts/llm_eval_utils.py check-deployment --results evaluation_results.csv --threshold 85`

**What it does:**

- Validates if evaluation results meet stricter deployment criteria
- Uses a (typically higher) threshold for production deployments
- Returns a success or failure status that can block deployment if not met
- Acts as a final quality gate before production releases

**Why it's important:**

- Provides an additional safeguard specifically for production deployments
- Allows teams to set higher quality standards for deployment vs. development
- Prevents pushing underperforming models to production users
- Creates a clear distinction between acceptable quality for testing and for production use

## Advanced Configuration

### Scheduled Evaluations

You can configure scheduled evaluations to run periodically:

```yaml
llm-evaluation-scheduled:
  stage: evaluate
  image: python:3.10-slim
  script:
    - pip install -r requirements.txt
    - python main.py --data $EVALUATION_DATASET --output evaluation_results.csv --metrics all
    - mkdir -p evaluation_history
    - cp evaluation_results.csv evaluation_history/$(date +%Y-%m-%d_%H-%M-%S).csv
    - python scripts/llm_eval_utils.py generate-trends --history-dir evaluation_history --output trends.png
  artifacts:
    paths:
      - evaluation_results.csv
      - evaluation_history/
      - trends.png
      - trends_data.csv
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  cache:
    paths:
      - evaluation_history/
```

### Testing Multiple Models

To evaluate and compare multiple models:

```yaml
.evaluation_template: &evaluation_definition
  stage: evaluate
  image: python:3.10-slim
  script:
    - pip install -r requirements.txt
    - python main.py --data $EVALUATION_DATASET --output ${MODEL_NAME}_results.csv --metrics all
  artifacts:
    paths:
      - ${MODEL_NAME}_results.csv

evaluate-gpt4:
  <<: *evaluation_definition
  variables:
    MODEL_NAME: 'gpt-4o'

evaluate-gpt35:
  <<: *evaluation_definition
  variables:
    MODEL_NAME: 'gpt-3.5-turbo'

compare-models:
  stage: evaluate
  image: python:3.10-slim
  needs:
    - evaluate-gpt4
    - evaluate-gpt35
  script:
    - pip install -r requirements.txt matplotlib seaborn
    - python scripts/llm_eval_utils.py compare-models --results1 gpt-4o_results.csv --results2 gpt-3.5-turbo_results.csv --output model_comparison.html
  artifacts:
    paths:
      - model_comparison.html
      - model_comparison.png
```

## Monitoring and Visualization

You can enhance your GitLab integration with monitoring and visualization:

1. **GitLab Metrics Dashboard**: The metrics exported to `metrics_report.txt` can be visualized in GitLab's built-in metrics dashboard.

2. **Historical Trend Analysis**: Store and analyze evaluation results over time:

```yaml
after_script:
  - mkdir -p evaluation_history
  - cp evaluation_results.csv evaluation_history/$(date +%Y-%m-%d_%H-%M-%S).csv
  - python scripts/llm_eval_utils.py generate-trends --history-dir evaluation_history --output trends.png
```

3. **GitLab Pages**: You can publish evaluation reports to GitLab Pages:

```yaml
pages:
  stage: deploy
  dependencies:
    - llm-evaluation
  script:
    - mkdir -p public
    - python scripts/llm_eval_utils.py generate-report --results evaluation_results.csv --output public/index.html
    - cp evaluation_results.csv public/
    - cp evaluation_chart.png public/
  artifacts:
    paths:
      - public
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: If you hit rate limits, add retry logic or implement request throttling.

2. **Job Timeouts**: For large evaluation datasets, increase the job timeout in `.gitlab-ci.yml`:

   ```yaml
   llm-evaluation:
     timeout: 2h
   ```

3. **Memory Issues**: If you encounter memory errors, consider:

   ```yaml
   llm-evaluation:
     image: python:3.10
     variables:
       PYTHONUNBUFFERED: '1'
     before_script:
       - ulimit -v 4000000 # Limit virtual memory
   ```

### Getting Help

If you encounter issues with the LLM Evaluator CI/CD integration:

1. Check the job logs for error messages
2. Verify your API keys and environment variables
3. Try running the evaluation locally to debug
4. Open an issue in the project repository

## Best Practices

1. **Version Control Your Test Data**: Keep your evaluation dataset under version control to track changes over time.

2. **Regular Updates**: Update your evaluation dataset periodically to reflect new use cases and edge cases.

3. **Threshold Selection**: Choose appropriate thresholds based on your specific needs and gradually increase them as your models improve.

4. **Reviewable Reports**: Generate human-readable reports that can be easily reviewed during merge request approvals.

5. **Continuous Improvement**: Use the evaluation results to iteratively improve your LLM prompt engineering and model selection.

## Example Workflows

### Evaluating Production Readiness

```yaml
stages:
  - test
  - evaluate
  - deploy

llm-evaluation:
  stage: evaluate
  # Configuration as above

deploy:
  stage: deploy
  script:
    - echo "Deploying to production"
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  needs:
    - job: llm-evaluation
      artifacts: true
  before_script:
    - python scripts/llm_eval_utils.py check-deployment --results evaluation_results.csv --threshold 85 || (echo "Evaluation did not meet deployment criteria" && exit 1)
```

### A/B Testing

Configure your pipeline to evaluate two different versions of your prompts or models and compare the results:

```yaml
a-b-test:
  stage: evaluate
  script:
    - pip install -r requirements.txt matplotlib seaborn
    - python main.py --data test_data/version_a.csv --output version_a_results.csv
    - python main.py --data test_data/version_b.csv --output version_b_results.csv
    - python scripts/llm_eval_utils.py compare-models --results1 version_a_results.csv --results2 version_b_results.csv --model1 "Version A" --model2 "Version B" --output comparison_report.html
  artifacts:
    paths:
      - version_a_results.csv
      - version_b_results.csv
      - comparison_report.html
      - comparison_report.png
```

## Conclusion

Integrating the LLM Evaluator with your GitLab CI/CD pipeline provides automated quality control for your LLM applications. By continuously evaluating LLM responses against your test dataset, you can maintain high standards and identify issues before they affect your users.

The unified utility script (`llm_eval_utils.py`) simplifies this integration by providing a single tool with multiple commands for checking quality, generating reports, comparing models, and determining deployment readiness.

For further customization, refer to the [GitLab CI/CD documentation](https://docs.gitlab.com/ee/ci/) and the [DSPy documentation](https://dspy.ai).
