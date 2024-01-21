from os.path import dirname, join
from unittest import TestCase
from decimal import Decimal

from pytezos import ContractInterface

class MyContractTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.my = ContractInterface.from_file(join(dirname(__file__), '..', 'build', 'governance.tz'))
        cls.maxDiff = None
    
    def test_concat(self):
        res = self.my.call('bar').result(storage='foo')
        self.assertEqual('foobar', res.storage)