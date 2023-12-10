from . import models as m
from .utils import is_date_valid_for_submission, validate_date


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
        id = self.data.get("id")
        date = self.data.get("date")
        if not (id and date):
            raise ValueError("'id' and 'date' must specified.")
        try:
            id = int(id)
        except ValueError:
            raise ValueError("invalid 'id' value.")
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
            DeliveryDate=self.date, Item=self.id
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


class ValidateOrder:
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
        item = self.data.get("item")
        date = self.data.get("date")
        if not (item and date):
            raise ValueError(
                "'item', 'date' and 'quantity' parameters must specified."
            )
        try:
            item = int(item)
        except ValueError:
            raise ValueError("invalid 'item' value.")

        self.item = item
        self.date = date

    def _validate_date(self):
        date = validate_date(self.date)
        if not date:
            raise ValueError("invalid 'date' value.")
        is_valid = is_date_valid_for_submission(date)
        if not is_valid:
            raise ValueError(
                "your deadline for submission on this date is over."
            )

    def _validate_item(self):
        is_item_available = m.DailyMenuItem.objects.filter(
            AvailableDate=self.date, Item=self.item
        ).first()
        if not is_item_available:
            raise ValueError("item is not available in corresponding date.")

    def create_order(self, personnel: str):
        instance = m.OrderItem.objects.filter(
            Personnel=personnel, DeliveryDate=self.date, Item=self.item
        ).first()
        if instance:
            instance.Quantity += 1
            instance.save()
            return

        m.OrderItem.objects.create(
            Personnel=personnel,
            DeliveryDate=self.date,
            Item=self.item,
            Quantity=1,
        )
