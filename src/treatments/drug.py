"""Abstract Drug base class for treatments."""
from abc import ABC, abstractmethod


class Drug(ABC):
    """Abstract base for drugs applied during treatment."""

    def __init__(self, model):
        self.model = model

    def apply_to_type(self, type_id, effectiveness, action):
        """Apply an action to agents of a given type with probability `effectiveness`.

        Args:
            type_id: AgentType int ID.
            effectiveness: Probability of applying to each agent.
            action: Callable taking (agent) as argument.
        """
        for agent in self.model.iter_agents_by_type_id(type_id):
            if self.model.rng.random() < effectiveness:
                action(agent)

    @abstractmethod
    def step(self, proportion=1.0):
        ...
