SELECT
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS Id,
    item.ItemName,
    orderitem.DeliveryDate,
    SUM(CASE WHEN orderitem.DeliveryPlace = 'PAD' THEN orderitem.Quantity ELSE 0 END) AS PAD,
    SUM(CASE WHEN orderitem.DeliveryPlace = 'OTH' THEN orderitem.Quantity ELSE 0 END) AS OTH
FROM
    pors_orderitem AS orderitem
        INNER JOIN
    pors_item AS item ON item.id = orderitem.item_id
GROUP BY
    item.ItemName,
    orderitem.DeliveryDate;