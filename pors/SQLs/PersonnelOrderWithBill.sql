SELECT oi.DeliveryDate, oi.Quantity, oi.PricePerOne,
           i.id, i.ItemName, i.Image, i.CurrentPrice,
           i.Category_id, i.ItemDesc, oi.Personnel,
           o.SubsidyCap, o.PersonnelDebt, o.TotalPrice
    FROM pors_orderitem AS oi
    INNER JOIN pors_item AS i ON oi.Item_id = i.id
    INNER JOIN "Order" AS o ON o.Personnel = oi.Personnel AND o.DeliveryDate = oi.DeliveryDate
    WHERE oi.DeliveryDate between %s AND %s and oi.Personnel = %s
    ORDER BY oi.DeliveryDate