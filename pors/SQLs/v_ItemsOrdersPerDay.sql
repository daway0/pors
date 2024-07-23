-- تعداد ادم هایی که ایتم خاص رو سفارش دادند و توی ادمین به کار میره کنار هر ایتم
SELECT ROW_NUMBER() over (ORDER BY dmi.AvailableDate ) as Id, dmi.AvailableDate as [Date],
         dmi.Item_id AS Item,
          COUNT(oi.id) TotalOrders, dmi.TotalOrdersAllowed, dmi.TotalOrdersLeft 
FROM PersonnelService.dbo.pors_dailymenuitem dmi left JOIN
    PersonnelService.dbo.pors_orderitem oi
ON dmi.AvailableDate = oi.DeliveryDate AND dmi.Item_id = oi.Item_id
group by dmi.AvailableDate, dmi.Item_id, TotalOrdersAllowed , TotalOrdersLeft 