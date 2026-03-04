"""Abstract Drug base class for treatments."""
from abc import ABC, abstractmethod


class Drug(ABC):
    """Abstract base for drugs applied during treatment."""

    def __init__(self, model):
        self.model = model

    @abstractmethod
    def step(self, proportion=1.0):
        ...
