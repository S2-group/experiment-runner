import unittest

from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.CustomErrors.BaseError import BaseError


class TestFactorModelUniqueness(unittest.TestCase):
    def test_uniqueness(self):
        try:
            factorModel = FactorModel('example_factore', [1,2,1])
            self.assertFalse('')
        except BaseError:
            pass


if __name__ == '__main__':
    unittest.main()
