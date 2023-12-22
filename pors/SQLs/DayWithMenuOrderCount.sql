SELECT menu.AvailableDate ,COUNT([Order].Id) AS OrderCount
FROM (
    select distinct AvailableDate
    from pors_dailymenuitem
     ) AS menu
         LEFT JOIN [Order]
                   ON [Order].DeliveryDate = menu.AvailableDate
GROUP BY menu.AvailableDate