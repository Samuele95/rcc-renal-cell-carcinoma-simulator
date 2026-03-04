"""Treatment — composition of drugs applied to a patient."""


class Treatment:
    """A treatment is a composition of drugs whose effects are proportionally averaged."""

    def __init__(self, drugs):
        self.drugs = drugs

    def step(self):
        if not self.drugs:
            return
        for drug in self.drugs:
            drug.step(proportion=1.0 / len(self.drugs))
