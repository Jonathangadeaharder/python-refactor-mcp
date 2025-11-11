"""
Utility functions for testing cross-file refactoring.

This file imports and uses functions from main.py to test that
refactoring operations correctly handle cross-file references.
"""

from typing import List
from .main import calculate_total, DataProcessor


def calculate_average(items: List[int]) -> float:
    """Calculate the average using calculate_total."""
    if not items:
        return 0.0
    total = calculate_total(items)  # Cross-file reference
    return total / len(items)


def create_processor(name: str) -> DataProcessor:
    """Create a DataProcessor instance."""
    return DataProcessor(name)  # Cross-file reference


def test_processor():
    """Test the DataProcessor class."""
    proc = create_processor("TestProcessor")
    proc.increment()
    return proc.get_status()
