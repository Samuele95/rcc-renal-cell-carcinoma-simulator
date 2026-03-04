"""TumorCell agent with glucose consumption (Warburg effect).

Ported from Mesa to Repast4Py with added glucose system integration.
"""
from collections import deque

from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.dna import DNA
from src.systems import grid_utils


class TumorCell(Cell):
    angiogenesis_effect = 0.0005
    angiogenesis_min_distance = 30
    angiogenesis_effect_collection_radius = 3
    injected_mutations = 3

    initial_tumor_growth = 0.1

    ICI_effect = False
    TKI_effect = False

    @staticmethod
    def add_blood(model):
        """Add a blood vessel via angiogenesis if conditions are met."""
        from src.agents.blood import Blood

        tumor_cells = model.get_agents_by_type_id(AgentType.TUMOR_CELL)
        if not tumor_cells:
            return
        selected = min(tumor_cells, key=lambda a: sum(a.pos[1:]) if a.pos else float('inf'))
        if selected.pos is None:
            return

        # Collect angiogenesis effect from neighbors
        neighbors = grid_utils.get_neighbors_3d(
            model.spatial_index, model.grid_dims, selected.pos,
            radius=TumorCell.angiogenesis_effect_collection_radius, moore=True
        )
        total_effect = selected.angiogenesis_effect
        for neighbor in neighbors:
            if neighbor.uid[1] == AgentType.TUMOR_CELL:
                total_effect += neighbor.experienced_effects.angiogenesis_effect

        if model.rng.random() < model.weight_params.w_tumor_angiogenesis * total_effect:
            # Find most distant non-tumor blood cell
            blood_neighbors = grid_utils.get_neighbors_3d(
                model.spatial_index, model.grid_dims, selected.pos,
                radius=TumorCell.angiogenesis_min_distance, moore=True
            )
            candidates = [b for b in blood_neighbors
                          if b.uid[1] == AgentType.BLOOD
                          and not b.is_tumour_generated()]
            if candidates:
                target = max(candidates, key=lambda b: sum(b.pos[1:]) if b.pos else 0)

                dx = target.pos[0] - selected.pos[0]
                dy = target.pos[1] - selected.pos[1]
                dz = target.pos[2] - selected.pos[2]

                x, y, z = selected.pos
                for i in range(abs(dx)):
                    b = Blood(model.next_id(), model.rank, model, None, tumour_generated=True)
                    b.pos = (x + (i + 1 if dx > 0 else -i - 1), y, z)
                    model.add_agent(b)
                x = x + dx

                for i in range(abs(dy)):
                    b = Blood(model.next_id(), model.rank, model, None, tumour_generated=True)
                    b.pos = (x, y + (i + 1 if dy > 0 else -i - 1), z)
                    model.add_agent(b)
                y = y + dy

                for i in range(abs(dz)):
                    b = Blood(model.next_id(), model.rank, model, None, tumour_generated=True)
                    b.pos = (x, y, z + (i + 1 if dz > 0 else -i - 1))
                    model.add_agent(b)

                selected.blood_access = True
                model.tumor_blood_sources.add(selected)

    @staticmethod
    def refresh_blood_access(model):
        """Update blood access for all tumor cells via BFS from blood sources."""
        source = deque(model.tumor_blood_sources)
        to_visit = set(model.tumor_blood_sources)
        visited = set()

        for agent in model.get_agents_by_type_id(AgentType.TUMOR_CELL):
            if agent not in to_visit:
                agent.blood_access = False

        while source:
            t = source.popleft()
            to_visit.discard(t)
            if t.pos is not None:
                neighbors = grid_utils.get_neighbors_3d(
                    model.spatial_index, model.grid_dims, t.pos, radius=1, moore=True
                )
                for neighbor in neighbors:
                    if (neighbor.uid[1] == AgentType.TUMOR_CELL):
                        neighbor.blood_access = True
                        if neighbor not in visited and neighbor not in to_visit:
                            source.append(neighbor)
                            to_visit.add(neighbor)
                visited.add(t)
            else:
                model.tumor_blood_sources.discard(t)

    def __init__(self, local_id, rank, model, pos, dna=None):
        super().__init__(local_id, AgentType.TUMOR_CELL, rank, model, pos)
        self.dna = dna if dna else DNA(model.rng, injected_mutations=self.injected_mutations)
        self.blood_access = False

        self.experienced_effects.tumour_growth_effect += self.initial_tumor_growth
        self.experienced_effects.angiogenesis_effect += self.angiogenesis_effect

    def step(self):
        # Glucose consumption (Warburg effect)
        self.consume_glucose(self.model.weight_params.w_glucose_tumor_consumption)

        # Tumor Apoptosis
        p_apoptosis = (
            self.experienced_effects.tumour_apoptosis_effect * self.model.weight_params.w_tumor_apoptosis_eff +
            self.model.weight_params.b_tumor_apoptosis
        )
        if self.model.rng.random() < p_apoptosis:
            p_extra_apoptosis = self.dna.tumor_suppression_chance * self.model.weight_params.w_tumor_apoptosis_dna
            if self.model.rng.random() < p_extra_apoptosis:
                self.record_kill()
                if self.TKI_effect:
                    # Release neoantigens to nearby dendritic cells (before removal nullifies pos)
                    neighbors = grid_utils.get_neighbors_3d(
                        self.model.spatial_index, self.model.grid_dims, self.pos, radius=3, moore=True
                    )
                    for dc in neighbors:
                        if dc.uid[1] == AgentType.DENDRITIC_CELL:
                            dc._phagocytosed_cell = self
                self.model.remove_agent(self)
                return

        # Tumor Duplication with glucose modulation
        tumor_growth_effect = self.experienced_effects.tumour_growth_effect
        if self.blood_access:
            tumor_growth_effect += (self.experienced_effects.angiogenesis_effect *
                                    self.model.weight_params.w_angiogenesis_tumor_growth)

        p_duplication = (
            (tumor_growth_effect * self.model.weight_params.w_tumor_growth_eff +
             self.dna.extra_proliferation_chance * self.model.weight_params.w_tumor_growth_dna) / 2 +
            self.model.weight_params.b_tumor_growth
        )

        # Glucose modulation of growth
        if self.pos is not None:
            glucose = self.model.glucose_field.get(self.pos)
            glucose_factor = min(1.0, glucose * self.model.weight_params.w_glucose_growth_sensitivity)
            p_duplication *= glucose_factor

        if self.model.rng.random() <= p_duplication:
            self.duplicate()

    def duplicate(self):
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
            antigens = list(self.dna.neo_antigens)
            if antigens:
                return self.model.rng.choice(antigens)
        return None

    def get_PD1_inhibition(self):
        """Whether this cell inhibits the PD-1 pathway of an interacting T cell."""
        if self.ICI_effect:
            return False
        p_inhibition = (self.dna.checkpoint_pathway_inhibition_chance *
                        self.model.weight_params.w_gene_pd1_inhibition)
        return self.model.rng.random() < p_inhibition

    needs_effect = True

    def tumour_growth_rate_value(self):
        """Return the tumor growth rate for terminal condition checking."""
        growth_potential = (
            self.experienced_effects.tumour_growth_effect * self.model.weight_params.w_tumor_growth_eff +
            self.dna.extra_proliferation_chance * self.model.weight_params.w_tumor_growth_dna
        )
        if self.blood_access:
            growth_potential += (self.experienced_effects.angiogenesis_effect *
                                 self.model.weight_params.w_angiogenesis_tumor_growth)
        p_apoptosis = (
            self.experienced_effects.tumour_apoptosis_effect * self.model.weight_params.w_tumor_apoptosis_eff +
            self.model.weight_params.b_tumor_apoptosis +
            self.dna.tumor_suppression_chance * self.model.weight_params.w_tumor_apoptosis_dna
        )
        tumor_growth_measure = self.sigmoid(growth_potential + p_apoptosis, k=10)
        return tumor_growth_measure


def restore_tumor_cell(uid, state):
    """Restore function for Repast4Py serialization."""
    from repast4py.core import Agent
    tc = TumorCell.__new__(TumorCell)
    Agent.__init__(tc, uid[0], uid[1], uid[2])
    tc.pos, tc._alive = state
    return tc
