import unittest

import jdatetime
from django.test import TestCase

from . import business as b
from .serializers import Deadline

# Create your tests here.


class TestDeadlineValidators(unittest.TestCase):
    def setUp(self) -> None:
        self.launch_deadlines = {
            0: Deadline(3, 16),
            1: Deadline(1, 16),
            2: Deadline(1, 16),
            3: Deadline(1, 16),
            4: Deadline(1, 16),
            5: Deadline(5, 15),
            6: Deadline(6, 14),
        }
        self.breakfast_deadlines = {
            0: Deadline(0, 14),
            1: Deadline(1, 14),
            2: Deadline(2, 14),
            3: Deadline(3, 14),
            4: Deadline(4, 14),
            5: Deadline(0, 11),
            6: Deadline(6, 14),
        }

    def test_saturday(self):
        mock_datetime = jdatetime.datetime(1403, 4, 16, 19)  # 0 weekday
        year, month, day = b.get_first_orderable_date(
            mock_datetime, self.breakfast_deadlines, self.launch_deadlines
        )
        self.assertEqual((year, month, day), (1403, 4, 19))

    # def test_is_date_valid_for_action(self):
    #     mock_datetime = jdatetime.datetime(1402, 9, 28, 13)
    #     target_date = "1402/09/28"
    #     result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
    #     self.assertEqual(result, False, "NAKHOY")

    #     mock_datetime = jdatetime.datetime(1402, 9, 28, 13)
    #     target_date = "1402/09/29"
    #     result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
    #     self.assertEqual(result, True, "NAKHOY")

    #     mock_datetime = jdatetime.datetime(1402, 9, 28, 15)
    #     target_date = "1402/09/29"
    #     result = b.is_date_valid_for_action(mock_datetime, target_date, 1, 14)
    #     self.assertEqual(result, False, "NAKHOY")
