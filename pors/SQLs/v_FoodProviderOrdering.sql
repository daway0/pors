select row_number() over (order by (select null)) as ID, pi.ItemName,
       pi.MealType,
       oi.PricePerOne,
       sum(oi.Quantity) ItemTotalCount,
       oi.DeliveryDate,
       oi.DeliveryBuilding,
       p.id as       FoodProvider,
       p.title as       FoodProviderPersian,
       Hc.Caption as       DeliveryBuildingPersian

from pors_orderitem oi
         inner join dbo.pors_item pi on oi.Item_id = pi.id
         inner join dbo.pors_itemprovider p on pi.ItemProvider_id = p.id
         inner join dbo.HR_constvalue Hc on oi.DeliveryBuilding = Hc.Code
where pi.Package_id is NULL
group by pi.ItemName, pi.MealType, oi.PricePerOne, oi.DeliveryDate, oi.DeliveryBuilding, p.title, p.id, Hc.Caption;




--use this ordering in backend
--order by oi.DeliveryDate, pi.MealType,FoodProvider, DeliveryBuilding

