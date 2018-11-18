import unittest

import datetime 

from context import TowngasBilling
from TowngasBilling.utils import *

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.dateformat = '%d-%b-%Y'
        self.datetimeformat = '%H:%M / %d-%m-%Y'
        self.datetime = datetime.datetime.now()
        self.date = datetime.date.today()

    def test_datetimeformat(self):
        self.assertEqual(self.datetime.strftime(self.datetimeformat), datetimeformat(self.datetime))

    def test_dateformat(self):
        self.assertEqual(self.date.strftime(self.dateformat), dateformat(self.date))

    def test_datemath(self):
        tomorrow = self.date + datetime.timedelta(days=1)
        self.assertEqual(dateformat(tomorrow), datemath(dateformat(self.date, "%d-%b-%y"), days=+1))
        


if __name__ == '__main__':
    unittest.main()
