"""Module for summarizer."""
from abc import ABC, abstractmethod


class Summarizer(ABC):
    """Abstract summarizer class."""

    @abstractmethod
    def summarize(self):
        """Summarize information."""
