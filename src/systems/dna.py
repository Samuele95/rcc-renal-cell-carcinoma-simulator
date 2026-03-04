from typing import Dict
from random import Random
import Levenshtein
import numpy as np


class DNA:
    gene_metadata: Dict[str, Dict] = {
        "MHC": {"start": 100, "length": 90, "wildtype": "YLGRCSCRLYDLPRSVIWDR"},
        "B2M": {"start": 300, "length": 90, "wildtype": "LILLCAKKRSEMKKCNVHMR"},
        "CD274": {"start": 500, "length": 90, "wildtype": "IWWEWVLGREFQEGSENDWY"},
        "BRCA1": {"start": 700, "length": 90, "wildtype": "PPENMSSILFSKFDQDMHPL"},
        "TP53": {"start": 900, "length": 90, "wildtype": "FGDRAKAYTHCTRSKTSRQL"},
        "RB1": {"start": 1100, "length": 90, "wildtype": "QHSIRQWGWFQPNIGVEREY"},
        "CDKN2A": {"start": 1300, "length": 90, "wildtype": "PSDFAYVAHYCMEMIERWCW"},
        "MYC": {"start": 1500, "length": 90, "wildtype": "YWKYAASEANRTSLRVVRMH"},
        "RAS": {"start": 1700, "length": 90, "wildtype": "RTEISHPCWVDHGDSDHART"},
        "EGFR": {"start": 1900, "length": 90, "wildtype": "NRQDTSYWGLRLSTDHLKFV"},
        "HER2": {"start": 2100, "length": 90, "wildtype": "NEPSSHLPWPNIQGSNGKQP"},
        "JAK1": {"start": 2300, "length": 90, "wildtype": "TGPHWRLNELCSEMGGHNKV"},
        "JAK2": {"start": 2500, "length": 90, "wildtype": "TPCELIWWDSWWITSFWYCQ"},
        "TAP1": {"start": 2700, "length": 90, "wildtype": "ANSNNICQFPDGLWKRHLEK"},
        "TAP2": {"start": 2900, "length": 90, "wildtype": "LRTLWATQDLRSWLWPWLSD"},
        "APC": {"start": 3100, "length": 90, "wildtype": "GQIYNHVLITETKGECWRSC"}
    }

    _self_antigens: set = None

    @classmethod
    def self_antigens(cls) -> set:
        if cls._self_antigens is None:
            cls._self_antigens = {
                wt[i: i + 10]
                for info in cls.gene_metadata.values()
                for wt in [info["wildtype"]]
                for i in range(len(wt) - 9)
            }
        return cls._self_antigens

    codon_table: Dict[str, str] = {
        'ATA': 'I', 'ATC': 'I', 'ATT': 'I', 'ATG': 'M',
        'ACA': 'T', 'ACC': 'T', 'ACG': 'T', 'ACT': 'T',
        'AAC': 'N', 'AAT': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGC': 'S', 'AGT': 'S', 'AGA': 'R', 'AGG': 'R',
        'CTA': 'L', 'CTC': 'L', 'CTG': 'L', 'CTT': 'L',
        'CCA': 'P', 'CCC': 'P', 'CCG': 'P', 'CCT': 'P',
        'CAC': 'H', 'CAT': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGA': 'R', 'CGC': 'R', 'CGG': 'R', 'CGT': 'R',
        'GTA': 'V', 'GTC': 'V', 'GTG': 'V', 'GTT': 'V',
        'GCA': 'A', 'GCC': 'A', 'GCG': 'A', 'GCT': 'A',
        'GAC': 'D', 'GAT': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGA': 'G', 'GGC': 'G', 'GGG': 'G', 'GGT': 'G',
        'TCA': 'S', 'TCC': 'S', 'TCG': 'S', 'TCT': 'S',
        'TTC': 'F', 'TTT': 'F', 'TTA': 'L', 'TTG': 'L',
        'TGT': 'C', 'TGC': 'C', 'TGA': '_', 'TGG': 'W',
        'TAC': 'Y', 'TAT': 'Y', 'TAA': '_', 'TAG': '_',
    }

    _codon_table_inv: Dict[str, str] = None

    @classmethod
    def codon_table_inv(cls) -> Dict[str, str]:
        if cls._codon_table_inv is None:
            cls._codon_table_inv = {v: k for k, v in cls.codon_table.items()}
        return cls._codon_table_inv

    @staticmethod
    def get_wildtype_dna_sequence(rng: Random) -> str:
        parts = []
        for gene, info in DNA.gene_metadata.items():
            parts.append(DNA.random_nucleotide_sequence(100, rng))
            parts.append(DNA.random_nucleotide_sequence(13, rng))
            parts.append('TATA')
            parts.append(DNA.random_nucleotide_sequence(13, rng))
            parts.append(DNA.protein_to_gene(info["wildtype"]))
            parts.append('TAA')
            parts.append(DNA.random_nucleotide_sequence(7, rng))
        return ''.join(parts)

    @staticmethod
    def random_nucleotide_sequence(length: int, rng: Random) -> str:
        if length <= 0:
            raise ValueError("Length must be a positive integer.")
        return ''.join(rng.choices('ATCG', k=length))

    @staticmethod
    def protein_to_gene(protein: str) -> str:
        inv = DNA.codon_table_inv()
        return ''.join(inv[aa] for aa in protein)

    antigen_presentation_chance: float
    checkpoint_pathway_inhibition_chance: float
    genomic_instability: float
    tumor_suppression_chance: float
    extra_proliferation_chance: float

    def __init__(self, rng: Random, dna_sequence: str = None, injected_mutations: int = 0):
        self.random = rng
        self.dna = dna_sequence if dna_sequence is not None else self.get_wildtype_dna_sequence(rng)

        if injected_mutations > 0:
            self.dna = (self.dna[:730] +
                        self.protein_to_gene(
                            self._mutate_string(
                                self.gene_metadata["BRCA1"]["wildtype"], injected_mutations)) +
                        self.dna[790:])

        self.expression = {}
        self.proteins = {}
        self.mutation_score = {}

        self._build_effects()

        self.neo_antigens = {protein[i: i + 10] for protein in self.proteins.values() for i in range(max(0, len(protein) - 9))}

    # Pre-computed alternatives for each base (avoids per-mutation list allocation)
    _MUTATION_MAP = {'A': 'TCG', 'T': 'ACG', 'C': 'ATG', 'G': 'ATC'}

    def duplicate(self) -> 'DNA':
        if self.genomic_instability == 0.0:
            return DNA(rng=self.random, dna_sequence=self.dna)

        new_dna = list(self.dna)
        length = len(new_dna)
        num_mutations = int(self.genomic_instability * length)
        mutation_map = self._MUTATION_MAP

        for _ in range(num_mutations):
            idx = self.random.randint(0, length - 1)
            new_dna[idx] = self.random.choice(mutation_map[new_dna[idx]])

        return DNA(rng=self.random, dna_sequence=''.join(new_dna))

    def gene_to_protein(self, gene_name: str) -> str:
        parts = []
        start = DNA.gene_metadata[gene_name]["start"]
        for i in range(start, len(self.dna) - 2, 3):
            codon = self.dna[i:i + 3]
            aa = self.codon_table.get(codon, 'X')
            if aa == '_':
                break
            parts.append(aa)
        return ''.join(parts)

    @staticmethod
    def gene_expr_to_chance(x, k=0.01):
        return 1 - np.exp(-k * x)

    def get_mutation_mask(self, wildtype_sequence: str) -> list:
        mutation_mask = []
        for ammino1, ammino2 in zip(wildtype_sequence, self.dna):
            mutation_mask.append(1 if ammino1 != ammino2 else 0)
        return mutation_mask

    def _build_effects(self):
        for gene, info in DNA.gene_metadata.items():
            start = info["start"]
            promoter = self.dna[start:start + 30]

            expr = self._promoter_expression(promoter)
            protein = self.gene_to_protein(gene)
            mutation_score = self._mutation_score(gene, protein)

            self.expression[gene] = expr
            self.proteins[gene] = protein
            self.mutation_score[gene] = mutation_score

        self.antigen_presentation_chance = max(0.0, 6.0 - sum(
            self._gene_mutation_expression(gene_name)
            for gene_name in ["MHC", "JAK1", "JAK2", "B2M", "TAP1", "TAP2"]) / 6.0)
        self.checkpoint_pathway_inhibition_chance = self._gene_mutation_expression("CD274")
        self.genomic_instability = (self._mutation_score("BRCA1") ** max(1, self.expression["BRCA1"])) * 0.05
        self.tumor_suppression_chance = sum(
            self.expression[gene_name] * (1 - self.mutation_score[gene_name])
            for gene_name in ["TP53", "RB1", "CDKN2A"]) / 3.0
        raw_proliferation = sum(
            self.expression[gene_name] * (1 - self.mutation_score[gene_name])
            for gene_name in ["MYC", "RAS", "EGFR", "HER2"]) / 5.0 + \
                             self._gene_mutation_expression("APC") / 5.0
        self.extra_proliferation_chance = self.gene_expr_to_chance(raw_proliferation)

    def _mutate_string(self, original: str, distance: int) -> str:
        if distance > len(original):
            raise ValueError("Edit distance cannot be greater than string length.")
        alphabet = 'ADCDEFGHIKLMNPQRSTVWY'
        positions = self.random.sample(range(len(original)), distance)
        original_list = list(original)
        for pos in positions:
            current_char = original_list[pos]
            alternatives = [c for c in alphabet if c != current_char]
            new_char = self.random.choice(alternatives)
            original_list[pos] = new_char
        return ''.join(original_list)

    def _gene_mutation_expression(self, gene_name: str):
        return self.expression[gene_name] * self.mutation_score[gene_name]

    def _promoter_expression(self, promoter: str) -> int:
        return promoter.count("TATA")

    def _mutation_score(self, gene_name: str, protein: str = None) -> float:
        ref = DNA.gene_metadata[gene_name]["wildtype"]
        if protein is None:
            protein = self.gene_to_protein(gene_name)
        similarity = Levenshtein.ratio(ref, protein)
        return 1.0 - similarity
