from . import models as m
from .utils import validate_date


class ValidateRemove:
    def __init__(self, request_data) -> None:
        self.data: dict = request_data

    def is_valid(self):
        try:
            self._validate_request()
            self._validate_date()
            self._validate_item()
        except ValueError as e:
            self.error = str(e)
            return False
        return True

    def _validate_request(self):
        id = int(self.data.get("id"))
        date = self.data.get("date")
        if not (id and date):
            raise ValueError("'id' and 'date' must specified.")
        self.date = date
        self.id = id

    def _validate_date(self):
        date = validate_date(self.date)
        if not date:
            raise ValueError("Date is not valid.")

    def _validate_item(self):
        instance = m.DailyMenuItem.objects.filter(
            AvailableDate=self.date, Item=self.id, IsActive=True
        )
        if not instance:
            raise ValueError("Item does not exists in provided date.")
        orders = m.OrderItem.objects.filter(
            DeliveryDate=self.date, OrderedItem=self.id
        )
        if orders:
            raise ValueError(
                "This item is not eligable for deleting, an order has already"
                "owned this item."
            )

    def remove_item(self):
        date = self.data.get("date")
        item = self.data.get("id")
        m.DailyMenuItem.objects.get(AvailableDate=date, Item=item).delete()
