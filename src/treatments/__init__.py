# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Treatment module for RCC simulation.

Provides drug classes (ICI, TKI) and a Treatment composition layer
that proportionally applies multiple drugs per simulation step.
"""
from .drug import Drug
from .ici import ICIDrug
from .tki import TKIDrug
from .treatment import Treatment
