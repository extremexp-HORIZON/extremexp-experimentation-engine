#!/usr/bin/env python3
"""
Standalone script for converting .xxp DSL files to Kubeflow Pipelines
Can be run independently without installing the full package
"""

import sys
import os

# Add the parent directory to the path so we can import the converter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kubeflow.cli import cli

if __name__ == '__main__':
    cli()
