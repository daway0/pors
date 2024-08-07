SELECT row_number() OVER (ORDER BY
        (SELECT NULL)) AS Id,
       orders.Personnel,
       users.NationalCode,
       users.FirstName,
       users.LastName,
       item.ItemName,
       item.id         AS ItemId,
       orders.Quantity,
       item.MealType,
       item.CurrentPrice,
       provider.title  as Provider,
       orders.DeliveryDate,
       orders.DeliveryBuilding,
       orders.DeliveryFloor,
       dbp.Caption     AS DeliveryBuildingPersian,
       dfp.Caption     AS DeliveryFloorPersian
FROM PersonnelService.dbo.pors_orderitem AS orders
         INNER JOIN
     PersonnelService.dbo.pors_item AS item ON orders.item_id = item.id
         INNER JOIN
     PersonnelService.dbo.pors_itemprovider provider on provider.id = item.ItemProvider_id
         LEFT JOIN
     users ON users.username = orders.personnel
         INNER JOIN
     HR_constvalue AS dbp ON dbp.Code = orders.DeliveryBuilding
         INNER JOIN
     HR_constvalue AS dfp ON dfp.Code = orders.DeliveryFloor
    WHERE item.Package_id is NULL ;