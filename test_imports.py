#!/usr/bin/env python

try:
    import dspy

    print("Successfully imported dspy version:", dspy.__version__)
except ImportError as e:
    print("Failed to import dspy:", e)

try:
    import pandas

    print("Successfully imported pandas version:", pandas.__version__)
except ImportError as e:
    print("Failed to import pandas:", e)

try:
    import tqdm

    print("Successfully imported tqdm version:", tqdm.__version__)
except ImportError as e:
    print("Failed to import tqdm:", e)

import sys

print("\nPython path:")
for path in sys.path:
    print(f" - {path}")
