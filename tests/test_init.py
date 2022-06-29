import unittest

from bom_analysis import Q_


class TestDPA(unittest.TestCase):
    def test_dpa_init(self):
        damage = Q_(75, "dpa")
        assert damage.m == 75
        assert damage == Q_(75, "DPA")
        assert damage == Q_(75, "displacements_per_atom")
