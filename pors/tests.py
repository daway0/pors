import unittest

import jdatetime
from django.test import TestCase

from . import business as b
from . import models as m
from . import utils as u

# Create your tests here.


class TestDeadlineValidators(unittest.TestCase):
    def test_get_first_orderable_date(self):
        mock_datetime = jdatetime.datetime(1402, 9, 9, 17)
        year, month, day = b.get_first_orderable_date(mock_datetime, 1, 14)
        self.assertEqual((year, month, day), (1402, 9, 11), "BLYAAAAAAAAT")

        mock_datetime = jdatetime.datetime(1402, 9, 9, 10)
        year, month, day = b.get_first_orderable_date(mock_datetime, 0, 15)
        self.assertEqual((year, month, day), (1402, 9, 9), "BLYAAAAAAAAT")

    def test_is_date_valid_for_action(self):
        mock_datetime = jdatetime.datetime(1402, 9, 28, 13)
        target_date = "1402/09/28"
        result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
        self.assertEqual(result, False, "NAKHOY")

        mock_datetime = jdatetime.datetime(1402, 9, 28, 13)
        target_date = "1402/09/29"
        result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
        self.assertEqual(result, True, "NAKHOY")

        mock_datetime = jdatetime.datetime(1402, 9, 28, 15)
        target_date = "1402/09/29"
        result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
        self.assertEqual(result, False, "NAKHOY")


class TestValidateRemove(unittest):
    def test_is_valid(self):
        item = m.Item.objects.filter(IsActive=True).first()
        m.DailyMenuItem.objects.filter(
            Item=item, IsActive=True, AvailableDate="1402/09/29"
        )
        mock_data = {"date": "1402/09/29", "item": 1}
        validator = b.ValidateRemove()
