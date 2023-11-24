SELECT     ROW_NUMBER() over (ORDER BY dmi.AvailableDate ) as Id,dmi.AvailableDate as [Date], dmi.Item_id AS Item, COUNT(oi.id) TotalOrders
FROM        dbo.pors_dailymenuitem dmi left JOIN
                  dbo.pors_orderitem oi  ON dmi.AvailableDate = oi.DeliveryDate AND dmi.Item_id = oi.Item_id
group by     dmi.AvailableDate, dmi.Item_id