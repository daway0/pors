SELECT        dmi.AvailableDate AS Date, dmi.Item_id AS Item, COUNT(*) AS TotalOrders
FROM            dbo.pors_orderitem AS oi INNER JOIN
                         dbo.pors_dailymenuitem AS dmi ON dmi.AvailableDate = oi.DeliveryDate AND dmi.Item_id = oi.OrderedItem_id
GROUP BY dmi.AvailableDate, dmi.Item_id