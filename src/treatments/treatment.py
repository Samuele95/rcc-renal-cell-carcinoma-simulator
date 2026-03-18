# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Treatment — composition of drugs applied to a patient."""


class Treatment:
    """A treatment is a composition of drugs whose effects are proportionally averaged."""

    def __init__(self, drugs):
        """Initialize a treatment with a list of drugs.

        Args:
            drugs: List of Drug instances to apply each step.
        """
        self.drugs = drugs

    def step(self):
        """Apply all drugs for one simulation step.

        Each drug receives an equal proportion (1/N) so that combined
        effectiveness sums to 1.0 when all drugs are active.
        """
        if not self.drugs:
            return
        for drug in self.drugs:
            drug.step(proportion=1.0 / len(self.drugs))
