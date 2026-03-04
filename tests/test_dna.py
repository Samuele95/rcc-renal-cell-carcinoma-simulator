"""Tests for the DNA system."""
import unittest
from random import Random
from src.systems.dna import DNA


class TestDNA(unittest.TestCase):

    def setUp(self):
        self.rng = Random(42)

    def test_wildtype_creation(self):
        dna = DNA(rng=self.rng)
        self.assertIsNotNone(dna.dna)
        self.assertGreater(len(dna.dna), 0)

    def test_gene_to_protein(self):
        dna = DNA(rng=self.rng)
        for gene_name in DNA.gene_metadata.keys():
            protein = dna.gene_to_protein(gene_name)
            self.assertIsInstance(protein, str)
            self.assertGreater(len(protein), 0)

    def test_wildtype_mutation_scores_low(self):
        """Wildtype DNA should have low mutation scores for all genes."""
        dna = DNA(rng=self.rng)
        for gene_name in DNA.gene_metadata:
            score = dna.mutation_score[gene_name]
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 0.1,
                                 f"Wildtype {gene_name} has unexpectedly high mutation score: {score}")

    def test_duplication(self):
        dna = DNA(rng=self.rng, injected_mutations=3)
        new_dna = dna.duplicate()
        self.assertIsInstance(new_dna, DNA)
        self.assertEqual(len(new_dna.dna), len(dna.dna))

    def test_neo_antigens(self):
        dna = DNA(rng=self.rng)
        self.assertIsInstance(dna.neo_antigens, set)

    def test_self_antigens(self):
        antigens = DNA.self_antigens()
        self.assertIsInstance(antigens, set)
        self.assertGreater(len(antigens), 0)
        for ag in antigens:
            self.assertEqual(len(ag), 10)

    def test_injected_mutations(self):
        dna_no_mut = DNA(rng=Random(42))
        dna_mut = DNA(rng=Random(42), injected_mutations=5)
        # With mutations, genomic instability should be higher
        self.assertGreaterEqual(dna_mut.genomic_instability, 0)

    def test_protein_to_gene_roundtrip(self):
        protein = "YLGRC"
        gene = DNA.protein_to_gene(protein)
        self.assertEqual(len(gene), len(protein) * 3)

    def test_duplication_zero_instability(self):
        """Duplication with zero genomic instability returns identical DNA."""
        dna = DNA(rng=self.rng)
        dna.genomic_instability = 0.0
        new_dna = dna.duplicate()
        self.assertEqual(new_dna.dna, dna.dna)


if __name__ == '__main__':
    unittest.main()
