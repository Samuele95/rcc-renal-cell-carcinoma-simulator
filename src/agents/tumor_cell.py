# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""TumorCell agent with glucose consumption (Warburg effect).

Ported from Mesa to Repast4Py with added glucose system integration.
"""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.dna import DNA
from src.systems import grid_utils


class TumorCell(Cell):
    """Renal cell carcinoma tumor cell agent.

    Models the Warburg effect (aerobic glycolysis), angiogenesis signaling,
    immune evasion via PD-1 checkpoint inhibition, and DNA-driven mutation
    dynamics. Growth and apoptosis are modulated by local glucose, neighboring
    cell effects, and treatment state (ICI/TKI).

    Attributes:
        dna: DNA instance encoding mutations, neoantigens, and suppression.
        blood_access: Whether this cell is adjacent to a blood vessel.
        ICI_effect: Whether immune checkpoint inhibitor treatment is active.
        TKI_effect: Whether tyrosine kinase inhibitor treatment is active.
    """

    angiogenesis_effect = 0.0005
    default_injected_mutations = 3

    initial_tumor_growth = 0.1

    # NOTE: ICI_effect and TKI_effect are initialized per-instance in __init__

    def __init__(self, local_id, rank, model, pos, dna=None):
        """Initialize a tumor cell.

        Args:
            local_id: Unique agent ID.
            rank: MPI rank.
            model: The RCCModel instance.
            pos: (x, y, z) grid position.
            dna: Optional DNA instance; generates new DNA if None.
        """
        super().__init__(local_id, AgentType.TUMOR_CELL, rank, model, pos)
        injected = getattr(model, 'injected_mutations', self.default_injected_mutations)
        self.dna = dna if dna else DNA(model.rng, injected_mutations=injected)
        self.blood_access = False
        self.ICI_effect = False
        self.TKI_effect = False

        self.experienced_effects.tumour_growth_effect += self.initial_tumor_growth
        self.experienced_effects.angiogenesis_effect += self.angiogenesis_effect

    def step(self):
        """Execute one simulation tick: consume glucose, check apoptosis, attempt duplication."""
        # Glucose consumption (Warburg effect)
        self.consume_glucose(self.model.weight_params.w_glucose_tumor_consumption)

        # Tumor Apoptosis
        if self.model.rng.random() < self._apoptosis_probability():
            p_extra = self.dna.tumor_suppression_chance * self.model.weight_params.w_tumor_apoptosis_dna
            if self.model.rng.random() < p_extra:
                self.record_kill()
                if self.TKI_effect:
                    # Release neoantigens to nearby dendritic cells (before removal nullifies pos)
                    neighbors = grid_utils.get_neighbors_3d(
                        self.model.spatial_index, self.model.grid_dims, self.pos, radius=3, moore=True
                    )
                    for dc in neighbors:
                        if dc.uid[1] == AgentType.DENDRITIC_CELL and dc.can_receive_neoantigen():
                            dc.receive_neoantigen(self)
                            break
                self.model.remove_agent(self)
                return

        # Tumor Duplication with glucose modulation
        p_duplication = self._growth_potential()

        if self.pos is not None:
            glucose = self.model.glucose_field.get(self.pos)
            glucose_factor = min(1.0, glucose * self.model.weight_params.w_glucose_growth_sensitivity)
            p_duplication *= glucose_factor

        if self.model.rng.random() <= p_duplication:
            self.duplicate()

    def duplicate(self):
        """Duplicate into an adjacent empty position, passing mutated DNA to the daughter cell."""
        if self.pos is None:
            return
        empty_ngbhs = self.get_empty_ngbhs()
        if not empty_ngbhs:
            return
        new_pos = empty_ngbhs[0]
        new_cell = TumorCell(self.model.next_id(), self.model.rank, self.model, new_pos, dna=self.dna.duplicate())
        self.model.add_agent(new_cell)

    def get_antigen(self):
        """Return an antigen presented by this tumor cell, or None."""
        p_presentation = (
            self.dna.antigen_presentation_chance * self.model.weight_params.w_antigen_presentation +
            self.model.weight_params.b_antigen_presentation
        )
        if self.model.rng.random() < p_presentation:
            if self.dna.neo_antigens:
                return self.model.rng.choice(self.dna.neo_antigens)
        return None

    def get_PD1_inhibition(self):
        """Whether this cell inhibits the PD-1 pathway of an interacting T cell."""
        if self.ICI_effect:
            return False
        p_inhibition = (self.dna.checkpoint_pathway_inhibition_chance *
                        self.model.weight_params.w_gene_pd1_inhibition)
        return self.model.rng.random() < p_inhibition

    needs_effect = True

    def _growth_potential(self):
        """Compute raw growth potential from effects, DNA, and blood access."""
        wp = self.model.weight_params
        growth = self.experienced_effects.tumour_growth_effect
        if self.blood_access:
            growth += self.experienced_effects.angiogenesis_effect * wp.w_angiogenesis_tumor_growth
        return (growth * wp.w_tumor_growth_eff +
                self.dna.extra_proliferation_chance * wp.w_tumor_growth_dna) / 2 + wp.b_tumor_growth

    def _apoptosis_probability(self):
        """Compute base apoptosis probability from effects and DNA."""
        wp = self.model.weight_params
        return (self.experienced_effects.tumour_apoptosis_effect * wp.w_tumor_apoptosis_eff +
                wp.b_tumor_apoptosis)

    def tumour_growth_rate_value(self):
        """Return the tumor growth rate for terminal condition checking."""
        growth_potential = self._growth_potential()
        p_apoptosis = (
            self._apoptosis_probability() +
            self.dna.tumor_suppression_chance * self.model.weight_params.w_tumor_apoptosis_dna
        )
        return self.sigmoid(growth_potential + p_apoptosis, k=10)


def restore_tumor_cell(uid, state):
    """Restore function for Repast4Py serialization."""
    from repast4py.core import Agent
    tc = TumorCell.__new__(TumorCell)
    Agent.__init__(tc, uid[0], uid[1], uid[2])
    tc.pos, tc._alive = state
    return tc
