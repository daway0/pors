SELECT row_number() over (order by (select null)) as Id, orders.Personnel,
       users.NationalCode,
       users.FirstName,
       users.LastName,
       item.ItemName,
       item.id as   ItemId,
       orders.Quantity,
       orders.DeliveryDate,
       orders.DeliveryBuilding,
       orders.DeliveryFloor
FROM PersonnelService.dbo.pors_orderitem AS orders
         INNER JOIN PersonnelService.dbo.pors_item AS item
                    ON orders.item_id = item.id
         LEFT JOIN hr.dbo.users AS users
                   ON users.username = orders.personnel