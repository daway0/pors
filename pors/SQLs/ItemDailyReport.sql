SELECT Row_number()
       OVER (ORDER BY (SELECT null)) as Id,
       users.firstname as FirstName,
       users.lastname as LastName,
       count(*) as TotalOrders,
       SUM(orders.TotalPrice) as TotalCost,
       SUM(SubsidySpent) as TotalSubsidySpent,
       SUM(PersonnelDebt) as TotalPersonnelDebt

FROM   PersonnelService.dbo.[Order] AS orders
INNER JOIN hr.dbo.users AS users
            ON orders.Personnel = users.username
group by orders.Personnel,
         users.firstname,
         users.lastname