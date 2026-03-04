"""Main RCC simulation driver for Repast4Py.

Replaces Mesa's Model class with a plain Python class that manages:
- SharedContext + SharedGrid (3D, multiple occupancy, sticky borders)
- spatial_index dict for neighbor queries
- GlucoseField instance
- random.Random(seed) as self.rng
- Agent lifecycle (add, remove, move)
"""
import logging
import random
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

from mpi4py import MPI
from repast4py import context as ctx
from repast4py.space import SharedGrid, BorderType, OccupancyType
from repast4py.geometry import BoundingBox

from src.agents.agent_types import AgentType
from src.agents.tumor_cell import TumorCell
from src.agents.sex_hormone import SexHormone, SexHormoneType
from src.agents.cd8_t_cell import CD8NaiveTCell
from src.agents.cd8_cytotoxic_t_cell import CytotoxicTCell
from src.agents.cd4_t_cell import CD4NaiveTCell
from src.agents.cd4_t_cell_h1 import CD4Helper1TCell
from src.agents.cd4_t_cell_h2 import CD4Helper2TCell
from src.agents.regulatory_t_cell import TregCell
from src.agents.dendritic_cell import DendriticCell
from src.agents.plasmacitoid_dc import PlasmacitoidDendriticCell
from src.agents.macrophage_m1 import MacrophageM1
from src.agents.macrophage_m2 import MacrophageM2
from src.agents.natural_killer import NaturalKiller
from src.agents.mast_cell import MastCell
from src.agents.neutrophil import Neutrophil
from src.agents.cell import Cell
from src.systems.glucose_field import GlucoseField
from src.parameters.model_parameters import ModelParameters
from src.parameters.weight_parameters import WeightParameters
from src.parameters.patient_parameters import PatientParameters
from src.model.observer import Observer
from src.model.cell_adder import CellAdder
from src.model.measures_utils import get_dimension_from_volume, get_number_of_cells_from_concentration
from src.treatments.ici import ICIDrug
from src.treatments.tki import TKIDrug
from src.treatments.treatment import Treatment


class RCCModel:
    """Main RCC simulation model for Repast4Py."""

    initial_number_of_tumor_cells = 10
    max_tumor_cells = 2000

    def __init__(self, comm=None, **kwargs):
        self.comm = comm or MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()

        # Parameters
        self.model_params = ModelParameters(**kwargs)
        self.weight_params = WeightParameters(**kwargs)
        self.patient_params = PatientParameters(**kwargs)

        self.volume = self.model_params.volume
        self.block_size = self.model_params.block_size
        self.max_steps = self.model_params.max_steps

        # RNG
        seed = self.model_params.random_seed + self.rank
        self.rng = random.Random(seed)

        # Grid dimensions
        grid_dim = get_dimension_from_volume(self.volume, self.block_size)
        self.grid_dims = (grid_dim, grid_dim, grid_dim)
        w, h, d = self.grid_dims

        # Repast4Py context and grid
        self.context = ctx.SharedContext(self.comm)
        self.grid = SharedGrid(
            "grid", bounds=BoundingBox(0, w, 0, h, 0, d),
            borders=BorderType.Sticky,
            occupancy=OccupancyType.Multiple,
            buffer_size=0, comm=self.comm
        )
        self.context.add_projection(self.grid)

        # Spatial index for neighbor queries — sets for O(1) add/discard
        self.spatial_index = defaultdict(set)

        # Agent tracking by type — dicts for O(1) add/remove
        self._agents_by_type = defaultdict(dict)  # type_id -> {id(agent): agent}
        self._all_agents = {}  # id(agent) -> agent
        self._id_counter = 0

        # Model state
        self.steps = 0
        self.running = True
        self.survival = False
        self.observer = Observer()

        # Class-level state moved to model
        self.tumor_blood_sources = set()
        self.cell_search_dimension = 5

        # Glucose field
        self.glucose_field = GlucoseField(w, h, d, initial_concentration=1.0)

        # Sex hormone state
        self.starting_dna = None
        self.sex = self.patient_params.sex
        self._setup_hormone_chances()

        # Sex drift
        self.init_sex_drift(max_drift=self.weight_params.w_max_drift, n_steps=15)

        # Treatment
        self._setup_treatment()

        self.tumour_growth_threshold = self.weight_params.w_tumour_growth_threshold

        # Cell adder and initialization
        self.cell_adder = CellAdder(self)
        self._initialize_agents()

        # Data log
        self.data_log = []

    def _setup_hormone_chances(self):
        if self.sex == "M":
            self.estrogen_hormone_chance = 0.2
            self.progesterone_hormone_chance = 0.1
            self.testosterone_hormone_chance = 1.0
        else:
            self.estrogen_hormone_chance = 0.9
            self.progesterone_hormone_chance = 0.8
            self.testosterone_hormone_chance = 0.2

    def _setup_treatment(self):
        drug_map = {
            "None": [],
            "ICI": [ICIDrug(self)],
            "TKI": [TKIDrug(self)],
            "ICI+TKI": [ICIDrug(self), TKIDrug(self)],
        }
        self.treatment = Treatment(drug_map.get(self.patient_params.treatment, []))
        self.treatment_start = self.patient_params.treatment_start

    def _initialize_agents(self):
        def number(concentration):
            return get_number_of_cells_from_concentration(concentration, self.volume)

        agents_to_create = {
            CytotoxicTCell: number(self.patient_params.ctc_concentration),
            Neutrophil: number(self.patient_params.neutrophil_concentration),
            MastCell: number(self.patient_params.mast_cell_concentration),
            TregCell: number(self.patient_params.treg_concentration),
            PlasmacitoidDendriticCell: number(self.patient_params.pdc_concentration),
            CD4Helper1TCell: number(self.patient_params.th1_concentration),
            CD4Helper2TCell: number(self.patient_params.th2_concentration),
            DendriticCell: number(self.patient_params.dc_concentration),
            MacrophageM1: number(self.patient_params.m1_concentration),
            MacrophageM2: number(self.patient_params.m2_concentration),
            NaturalKiller: number(self.patient_params.nkl_concentration),
            CD4NaiveTCell: number(self.patient_params.cd4_concentration),
            CD8NaiveTCell: number(self.patient_params.cd8_concentration),
        }

        for agent_type, n in agents_to_create.items():
            self.cell_adder.add(agent_type, n=n)

        self.cell_adder.add_blood_vessels()

        TumorCell.injected_mutations = 3 if self.patient_params.sex == "M" else 1
        tumor_cell = self.cell_adder.add_single_cancer_cell()
        self.starting_dna = tumor_cell.dna.dna
        for _ in range(self.initial_number_of_tumor_cells):
            tumor_cell.duplicate()

    # ------------------------------------------------------------------
    # Agent management
    # ------------------------------------------------------------------

    def next_id(self):
        """Return the next unique agent ID."""
        self._id_counter += 1
        return self._id_counter

    def add_agent(self, agent):
        """Add an agent to the model, context, grid, and spatial index."""
        if agent.pos is None:
            agent.pos = self.random_position()

        agent_key = id(agent)
        self._all_agents[agent_key] = agent
        type_id = agent.uid[1]
        self._agents_by_type[type_id][agent_key] = agent

        # Add to Repast4Py context and grid
        self.context.add(agent)
        try:
            self.grid.move(agent, agent.pos)
        except Exception:
            logger.debug("Failed to move agent %s to %s on grid.add", agent.uid, agent.pos)

        # Update spatial index
        self.spatial_index[agent.pos].add(agent)

    def remove_agent(self, agent):
        """Remove an agent from the model. O(1) for dict-based tracking."""
        if not agent._alive:
            return
        agent._alive = False

        # Remove from spatial index (O(1) set discard)
        pos = agent.pos
        if pos is not None and pos in self.spatial_index:
            self.spatial_index[pos].discard(agent)

        # O(1) removal from dict-based tracking
        agent_key = id(agent)
        type_id = agent.uid[1]
        self._agents_by_type[type_id].pop(agent_key, None)
        self._all_agents.pop(agent_key, None)

        # Remove from Repast4Py context
        try:
            self.context.remove(agent)
        except Exception:
            pass

        agent.pos = None

    def move_agent(self, agent, new_pos):
        """Move an agent to a new position."""
        old_pos = agent.pos
        if old_pos is not None and old_pos in self.spatial_index:
            self.spatial_index[old_pos].discard(agent)

        agent.pos = new_pos
        self.spatial_index[new_pos].add(agent)

        try:
            self.grid.move(agent, new_pos)
        except Exception:
            logger.debug("Failed to move agent %s to %s on grid", agent.uid, new_pos)

    def get_agents_by_type_id(self, type_id):
        """Get all living agents of a given AgentType ID."""
        return list(self._agents_by_type.get(type_id, {}).values())

    def count_agents(self, type_id):
        """Count living agents of a given type."""
        return len(self._agents_by_type.get(type_id, {}))

    # ------------------------------------------------------------------
    # Position utilities
    # ------------------------------------------------------------------

    def random_position(self, entry_point=False):
        """Generate a random position in the grid."""
        w, h, d = self.grid_dims

        def border(dimension):
            return 0 if self.rng.random() < 0.5 else dimension - 1

        coords = [self.rng.randrange(0, w), self.rng.randrange(0, h), self.rng.randrange(0, d)]
        if entry_point:
            random_border = self.rng.randrange(0, 3)
            coords[random_border] = border(self.grid_dims[random_border])
        return tuple(coords)

    # ------------------------------------------------------------------
    # Sex drift
    # ------------------------------------------------------------------

    def init_sex_drift(self, max_drift=0.25, n_steps=10):
        self._remaining_drift_steps = n_steps
        self._drift_per_step = max_drift / n_steps
        self._drift_sign = -1 if self.sex == "F" else +1

    def apply_sex_drift(self):
        if self._remaining_drift_steps <= 0:
            return

        step_factor = 1 + self._drift_sign * self._drift_per_step
        delta = abs(step_factor - 1)

        population = self.get_agents_by_type_id(AgentType.CD8_NAIVE_T_CELL)

        if step_factor > 1:
            to_duplicate = [a for a in population if self.rng.random() < delta]
            for agent in to_duplicate:
                agent.duplicate()
        else:
            to_remove = [a for a in population if self.rng.random() < delta]
            for agent in to_remove:
                self.remove_agent(agent)

        self._remaining_drift_steps -= 1

    # ------------------------------------------------------------------
    # Hormone spawning
    # ------------------------------------------------------------------

    def spawn_hormones(self):
        vessels = self.get_agents_by_type_id(AgentType.BLOOD)
        if not vessels:
            return

        def _spawn(hormone_type, chance, n):
            for _ in range(n):
                if self.rng.random() < chance:
                    v = self.rng.choice(vessels)
                    if v.pos is not None:
                        h = SexHormone(self.next_id(), self.rank, self, v.pos, hormone_type)
                        self.add_agent(h)

        _spawn(SexHormoneType.ESTROGEN, self.estrogen_hormone_chance, 1)
        _spawn(SexHormoneType.PROGESTERONE, self.progesterone_hormone_chance, 1)
        _spawn(SexHormoneType.TESTOSTERONE, self.testosterone_hormone_chance, 1)

    # ------------------------------------------------------------------
    # Manage blood / search dimension
    # ------------------------------------------------------------------

    def manage_blood(self):
        TumorCell.add_blood(self)
        TumorCell.refresh_blood_access(self)

    def manage_search_dimension(self):
        n_tumor = self.count_agents(AgentType.TUMOR_CELL)
        self.cell_search_dimension = max(5, int(n_tumor // (10 * self.weight_params.w_search_dimension)))

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    # Agent types that have needs_effect = True
    _EFFECT_RECEIVER_TYPES = frozenset({
        AgentType.TUMOR_CELL, AgentType.NATURAL_KILLER, AgentType.CD8_CYTOTOXIC_T_CELL,
        AgentType.MACROPHAGE_M1, AgentType.MACROPHAGE_M2, AgentType.DENDRITIC_CELL,
        AgentType.CD4_HELPER1_T_CELL, AgentType.CD8_NAIVE_T_CELL, AgentType.CD4_NAIVE_T_CELL,
    })

    def apply_effects(self):
        for type_id in self._EFFECT_RECEIVER_TYPES:
            for agent in list(self._agents_by_type.get(type_id, {}).values()):
                if agent._alive:
                    agent.collect_and_apply_effects()

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move_all_agents(self):
        for agent in list(self._all_agents.values()):
            if isinstance(agent, Cell) and agent._alive and agent._desired_pos != agent.pos:
                self.move_agent(agent, agent._desired_pos)

    # ------------------------------------------------------------------
    # Terminal condition
    # ------------------------------------------------------------------

    def terminal_condition(self):
        if self.steps >= self.max_steps:
            return True, False

        n_tumor = self.count_agents(AgentType.TUMOR_CELL)
        if n_tumor == 0:
            return True, True

        if n_tumor >= self.max_tumor_cells:
            return True, False

        tumor_agents = self._agents_by_type.get(AgentType.TUMOR_CELL, {}).values()
        tumor_growth = sum(a.tumour_growth_rate_value() for a in tumor_agents) / n_tumor
        if tumor_growth >= self.tumour_growth_threshold:
            return True, False

        return False, False

    def check_termination(self):
        terminated, survival = self.terminal_condition()
        if terminated:
            self.running = False
            self.survival = survival
        return terminated

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def collect_data(self):
        """Collect current step data."""
        row = {
            'step': self.steps,
            'tumor_cells': self.count_agents(AgentType.TUMOR_CELL),
            'cytotoxic_t_cells': self.count_agents(AgentType.CD8_CYTOTOXIC_T_CELL),
            'cd8_naive': self.count_agents(AgentType.CD8_NAIVE_T_CELL),
            'cd4_naive': self.count_agents(AgentType.CD4_NAIVE_T_CELL),
            'th1': self.count_agents(AgentType.CD4_HELPER1_T_CELL),
            'th2': self.count_agents(AgentType.CD4_HELPER2_T_CELL),
            'treg': self.count_agents(AgentType.REGULATORY_T_CELL),
            'dendritic': self.count_agents(AgentType.DENDRITIC_CELL),
            'pdc': self.count_agents(AgentType.PLASMACITOID_DC),
            'm1': self.count_agents(AgentType.MACROPHAGE_M1),
            'm2': self.count_agents(AgentType.MACROPHAGE_M2),
            'nk': self.count_agents(AgentType.NATURAL_KILLER),
            'mast': self.count_agents(AgentType.MAST_CELL),
            'neutrophil': self.count_agents(AgentType.NEUTROPHIL),
            'adipocyte': self.count_agents(AgentType.ADIPOCYTE),
            'blood': self.count_agents(AgentType.BLOOD),
            'sex_hormone': self.count_agents(AgentType.SEX_HORMONE),
            'apoptosis_count': self.observer.apoptosis_count,
            'm1_kills': self.observer.m1_macrophage_kills,
            'dc_kills': self.observer.dendritic_cell_kills,
            'pdc_kills': self.observer.pdc_kills,
            'ctc_kills': self.observer.cytotoxic_T_cell_kills,
            'nkl_kills': self.observer.nkl_kill_count,
            'neutrophil_kills': self.observer.neutrophil_kills,
            'mean_glucose': self.glucose_field.mean_concentration(),
            'total_glucose': self.glucose_field.total_concentration(),
            'min_glucose': self.glucose_field.min_concentration(),
            'max_glucose': self.glucose_field.max_concentration(),
        }
        self.data_log.append(row)

    def log_data(self):
        """Write collected data to CSV."""
        if not self.data_log:
            return
        import csv
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "simulation_log.csv"
        with open(log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.data_log[0].keys())
            writer.writeheader()
            writer.writerows(self.data_log)

    # ------------------------------------------------------------------
    # Mutation mask
    # ------------------------------------------------------------------

    def current_mean_mutation_mask(self):
        tumor_cells = self.get_agents_by_type_id(AgentType.TUMOR_CELL)
        if not tumor_cells:
            return []
        mutation_masks = [t.dna.get_mutation_mask(self.starting_dna) for t in tumor_cells]
        seq_len = len(mutation_masks[0])
        mean_mask = [0] * seq_len
        for mask in mutation_masks:
            for i, bit in enumerate(mask):
                mean_mask[i] += bit
        return [count / len(mutation_masks) for count in mean_mask]

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self):
        """Execute one simulation step.

        Order: collect data → check termination → apply effects → treatment
               → sex drift → glucose field step → angiogenesis → search dimension
               → shuffle & step all agents → deferred move → spawn hormones
        """
        self.collect_data()

        if self.check_termination():
            self.log_data()
            return

        self.apply_effects()

        if self.steps >= self.treatment_start:
            self.treatment.step()

        self.apply_sex_drift()

        # Glucose field step (source injection, diffusion, decay)
        self.glucose_field.step(self)

        self.manage_blood()
        self.manage_search_dimension()

        # Shuffle and step all agents (snapshot to avoid mutation during iteration)
        agents_snapshot = list(self._all_agents.values())
        self.rng.shuffle(agents_snapshot)
        for agent in agents_snapshot:
            if agent._alive:
                agent.step()

        self.move_all_agents()
        self.spawn_hormones()

        self.steps += 1
