"""
Example Python file for testing the MCP server.

This file contains various Python constructs to test refactoring operations.
"""

from typing import List, Dict


def calculate_total(items: List[int]) -> int:
    """Calculate the total sum of items."""
    total = 0
    for item in items:
        total += item
    return total


def process_data(data: Dict[str, int]) -> Dict[str, int]:
    """Process data dictionary."""
    result = {}
    for key, value in data.items():
        result[key] = value * 2
    return result


class DataProcessor:
    """A class for processing data."""

    def __init__(self, name: str):
        self.name = name
        self.count = 0

    def increment(self):
        """Increment the counter."""
        self.count += 1

    def get_status(self) -> str:
        """Get the current status."""
        return f"{self.name}: {self.count}"


def main():
    """Main function."""
    # Test calculate_total
    numbers = [1, 2, 3, 4, 5]
    total = calculate_total(numbers)
    print(f"Total: {total}")

    # Test process_data
    data = {"a": 1, "b": 2, "c": 3}
    processed = process_data(data)
    print(f"Processed: {processed}")

    # Test DataProcessor
    processor = DataProcessor("Test")
    processor.increment()
    processor.increment()
    print(processor.get_status())


if __name__ == "__main__":
    main()
