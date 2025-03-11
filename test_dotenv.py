#!/usr/bin/env python
"""
Test script to verify that python-dotenv is working correctly.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
print("Loading .env file...")
load_dotenv()

# Display the loaded environment variables
print("\nEnvironment variables loaded:")
print(
    f"OPENAI_API_KEY: {'*' * 10 + os.environ.get('OPENAI_API_KEY')[-4:] if os.environ.get('OPENAI_API_KEY') else 'Not found'}"
)
print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', 'Not found')}")
print(f"MODEL_NAME: {os.environ.get('MODEL_NAME', 'Not found')}")
print(
    f"METRICS_THRESHOLD_RELEVANCY: {os.environ.get('METRICS_THRESHOLD_RELEVANCY', 'Not found')}"
)
print(
    f"METRICS_THRESHOLD_CORRECTNESS: {os.environ.get('METRICS_THRESHOLD_CORRECTNESS', 'Not found')}"
)
print(
    f"METRICS_THRESHOLD_ROUGE: {os.environ.get('METRICS_THRESHOLD_ROUGE', 'Not found')}"
)
print(f"OUTPUT_DIR: {os.environ.get('OUTPUT_DIR', 'Not found')}")
print(f"LOG_LEVEL: {os.environ.get('LOG_LEVEL', 'Not found')}")

print("\nVerifying dotenv version:")
try:
    from dotenv import __version__

    print(f"python-dotenv version: {__version__}")
except ImportError:
    print("Could not determine python-dotenv version")

if __name__ == "__main__":
    print("\nDotenv test completed successfully!")
