# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Simplified DNA and gene expression system for tumor cell agents.

Models a nucleotide sequence containing 16 cancer-related genes with promoter
regions, coding sequences, and stop codons. Mutations in the sequence alter
gene expression and derived phenotypic traits such as antigen presentation,
checkpoint inhibition, genomic instability, tumor suppression, and
proliferation.
"""
from typing import Dict
from random import Random
import Levenshtein
import numpy as np


class DNA:
    """Represents the DNA sequence and derived gene expression of a tumor cell.

    Each instance holds a nucleotide string encoding 16 genes. On construction
    the sequence is translated to proteins, expression levels are computed from
    promoter TATA-box counts, and mutation scores are derived via Levenshtein
    distance from wildtype. These feed into five phenotypic probabilities used
    by agent behaviour logic.

    Attributes:
        dna: The full nucleotide sequence string.
        expression: Per-gene expression level (TATA-box count).
        proteins: Per-gene translated amino acid string.
        mutation_score: Per-gene mutation score in [0, 1].
        neo_antigens: Tuple of unique 10-mer peptides from translated proteins.
        antigen_presentation_chance: Probability of MHC-I antigen presentation.
        checkpoint_pathway_inhibition_chance: PD-L1 pathway inhibition level.
        genomic_instability: Rate of new mutations during replication.
        tumor_suppression_chance: Aggregate tumor suppressor activity.
        extra_proliferation_chance: Oncogene-driven extra proliferation rate.
    """

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
        """Return the set of all wildtype 10-mer peptides (cached on first call)."""
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
        """Return the inverse codon table mapping amino acids to codons (cached)."""
        if cls._codon_table_inv is None:
            cls._codon_table_inv = {v: k for k, v in cls.codon_table.items()}
        return cls._codon_table_inv

    @staticmethod
    def get_wildtype_dna_sequence(rng: Random) -> str:
        """Generate a full wildtype DNA sequence with random intergenic regions.

        Args:
            rng: Random number generator for non-coding region generation.

        Returns:
            A nucleotide string containing all 16 genes with promoters and
            stop codons, separated by random intergenic sequences.
        """
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
        """Generate a random nucleotide string of the given length.

        Args:
            length: Number of bases (must be positive).
            rng: Random number generator.

        Returns:
            A string of A/T/C/G characters.
        """
        if length <= 0:
            raise ValueError("Length must be a positive integer.")
        return ''.join(rng.choices('ATCG', k=length))

    @staticmethod
    def protein_to_gene(protein: str) -> str:
        """Back-translate an amino acid sequence to a nucleotide coding sequence.

        Args:
            protein: Amino acid string.

        Returns:
            Nucleotide string (3 bases per amino acid).
        """
        inv = DNA.codon_table_inv()
        return ''.join(inv[aa] for aa in protein)

    antigen_presentation_chance: float = 0.0
    checkpoint_pathway_inhibition_chance: float = 0.0
    genomic_instability: float = 0.0
    tumor_suppression_chance: float = 0.0
    extra_proliferation_chance: float = 0.0

    def __init__(self, rng: Random, dna_sequence: str = None, injected_mutations: int = 0):
        """Initialize a DNA instance, translate genes, and compute phenotypic effects.

        Args:
            rng: Random number generator for mutations.
            dna_sequence: Pre-built nucleotide string, or None to generate wildtype.
            injected_mutations: Number of point mutations to inject into BRCA1
                at construction (used for sex-dependent initial instability).
        """
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

        self.neo_antigens = tuple({protein[i: i + 10] for protein in self.proteins.values() for i in range(max(0, len(protein) - 9))})

    # Pre-computed alternatives for each base (avoids per-mutation list allocation)
    _MUTATION_MAP = {'A': 'TCG', 'T': 'ACG', 'C': 'ATG', 'G': 'ATC'}

    def duplicate(self) -> 'DNA':
        """Create a daughter DNA copy, introducing mutations based on genomic instability.

        Returns:
            A new DNA instance with possible point mutations.
        """
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
        """Translate a gene's coding region into an amino acid sequence.

        Args:
            gene_name: Key into gene_metadata (e.g., "TP53").

        Returns:
            Amino acid string, stopping at the first stop codon.
        """
        parts = []
        info = DNA.gene_metadata[gene_name]
        # Skip the 30-base promoter region to reach coding sequence
        start = info["start"] + 30
        end = info["start"] + info["length"]
        for i in range(start, min(end, len(self.dna) - 2), 3):
            codon = self.dna[i:i + 3]
            aa = self.codon_table.get(codon, 'X')
            if aa == '_':
                break
            parts.append(aa)
        return ''.join(parts)

    @staticmethod
    def gene_expr_to_chance(x, k=0.01):
        """Convert a raw expression value to a probability via exponential saturation.

        Args:
            x: Raw gene expression value.
            k: Saturation rate constant.

        Returns:
            Probability in [0, 1).
        """
        return 1 - np.exp(-k * x)

    def get_mutation_mask(self, wildtype_sequence: str) -> list:
        """Compare this DNA against a wildtype sequence, returning a per-base mask.

        Args:
            wildtype_sequence: Reference nucleotide string.

        Returns:
            List of 0/1 ints, where 1 indicates a mutated position.
        """
        mutation_mask = []
        for ammino1, ammino2 in zip(wildtype_sequence, self.dna):
            mutation_mask.append(1 if ammino1 != ammino2 else 0)
        return mutation_mask

    def _build_effects(self):
        """Translate all genes and compute derived phenotypic probabilities."""
        for gene, info in DNA.gene_metadata.items():
            start = info["start"]
            promoter = self.dna[start:start + 30]

            expr = self._promoter_expression(promoter)
            protein = self.gene_to_protein(gene)
            mscore = self._compute_mutation_score(gene, protein)

            self.expression[gene] = expr
            self.proteins[gene] = protein
            self.mutation_score[gene] = mscore

        self.antigen_presentation_chance = max(0.0, 6.0 - sum(
            self._gene_mutation_expression(gene_name)
            for gene_name in ["MHC", "JAK1", "JAK2", "B2M", "TAP1", "TAP2"]) / 6.0)
        self.checkpoint_pathway_inhibition_chance = self._gene_mutation_expression("CD274")
        self.genomic_instability = (self.mutation_score["BRCA1"] ** max(1, self.expression["BRCA1"])) * 0.05
        self.tumor_suppression_chance = sum(
            self.expression[gene_name] * (1 - self.mutation_score[gene_name])
            for gene_name in ["TP53", "RB1", "CDKN2A"]) / 3.0
        raw_proliferation = sum(
            self.expression[gene_name] * (1 - self.mutation_score[gene_name])
            for gene_name in ["MYC", "RAS", "EGFR", "HER2"]) / 5.0 + \
                             self._gene_mutation_expression("APC") / 5.0
        self.extra_proliferation_chance = self.gene_expr_to_chance(raw_proliferation)

    def _mutate_string(self, original: str, distance: int) -> str:
        """Introduce a fixed number of amino acid substitutions into a protein string.

        Args:
            original: Amino acid sequence to mutate.
            distance: Number of positions to change.

        Returns:
            Mutated amino acid string.
        """
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
        """Return the product of expression level and mutation score for a gene."""
        return self.expression[gene_name] * self.mutation_score[gene_name]

    def _promoter_expression(self, promoter: str) -> int:
        """Count TATA-box motifs in a promoter region as an expression proxy."""
        return promoter.count("TATA")

    def _compute_mutation_score(self, gene_name: str, protein: str = None) -> float:
        """Compute the mutation score for a gene as 1 minus Levenshtein similarity.

        Args:
            gene_name: Key into gene_metadata.
            protein: Pre-translated protein, or None to translate on the fly.

        Returns:
            Score in [0, 1] where 0 means identical to wildtype.
        """
        ref = DNA.gene_metadata[gene_name]["wildtype"]
        if protein is None:
            protein = self.gene_to_protein(gene_name)
        similarity = Levenshtein.ratio(ref, protein)
        return 1.0 - similarity
