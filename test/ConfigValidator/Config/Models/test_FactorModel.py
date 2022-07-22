import unittest

from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.CustomErrors.BaseError import BaseError


class TestFactorModelUniqueness(unittest.TestCase):
    def test_uniqueness(self):
        try:
            factorModel = FactorModel('example_factor', [1, 2, 1])
            self.assert_(False)
        except BaseError:
            pass


if __name__ == '__main__':
    unittest.main()
