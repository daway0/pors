select pu.EmailAddress 
from PersonnelService.dbo.pors_user pu 
left join PersonnelService.dbo.[Order] o on o.Personnel = pu.Personnel and o.DeliveryDate = %s
and o.MealType = %s
where o.Id is NULL and pu.EmailNotif = 1