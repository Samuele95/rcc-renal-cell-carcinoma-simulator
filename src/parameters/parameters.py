# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Abstract base class for simulation parameter dataclasses.

All concrete parameter groups (Model, Patient, Weight) inherit from
Parameters, gaining dict-like access, safe keyword-based construction,
and serialization to plain dicts.
"""
import logging
from abc import ABC
from dataclasses import fields, dataclass, asdict
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class Parameters(ABC):
    """Base dataclass for simulation parameter groups.

    Subclasses define fields as dataclass attributes plus two ClassVars:
    ``param_labels`` (human-readable names) and ``param_steps`` (UI
    slider increments).  Unknown keyword arguments are silently ignored
    so that a superset dict can be passed safely.
    """

    param_labels: ClassVar[dict]
    param_steps: ClassVar[dict]

    def __init__(self, **kwargs):
        self.set_parameters(**kwargs)

    def set_parameters(self, **kwargs):
        """Set multiple parameters by name, ignoring unknown keys.

        Args:
            **kwargs: Parameter name-value pairs to set.
        """
        valid_params = self.parameter_set()
        for key, value in kwargs.items():
            if key in valid_params:
                setattr(self, key, value)
            else:
                logger.debug("Ignoring unknown parameter '%s' for %s", key, type(self).__name__)

    def parameter_set(self) -> set:
        """Return the set of valid parameter names for this dataclass."""
        return {f.name for f in fields(self)}

    def to_dict(self):
        """Serialize all parameters to a plain dict."""
        return asdict(self)

    def __getitem__(self, key):
        """Allow dict-style read access (e.g. ``params['volume']``)."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Allow dict-style write access; raises KeyError for unknown keys."""
        if not hasattr(self, key):
            raise KeyError(f"Parameter '{key}' does not exist.")
        setattr(self, key, value)
