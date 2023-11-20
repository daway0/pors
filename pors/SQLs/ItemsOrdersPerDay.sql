select dmi.AvailableDate, dmi.Item_id Item, count(*) OrderNumber
from pors_orderitem oi
inner join pors_dailymenuitem dmi on dmi.AvailableDate = oi.DeliveryDate and dmi.Item_id = oi.OrderedItem_id
group by dmi.AvailableDate, dmi.Item_id