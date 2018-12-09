import os
import sys


REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(REPO_DIR, "examples")
EXAMPLESCRAPER_DIR = os.path.join(EXAMPLES_DIR, "examplescraper")

# Enable `examplescraper` lookup as tests leverage it.
sys.path.insert(0, EXAMPLES_DIR)
