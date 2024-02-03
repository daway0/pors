SELECT Row_number() OVER (ORDER BY PersonnelService.dbo.pors_orderitem
.deliverydate) AS Id,
       HR.dbo.Users.NationalCode,
       HR.dbo.Users.FirstName,
       HR.dbo.Users.LastName,
       PersonnelService.dbo.pors_orderitem.Personnel                     as Personnel,
       PersonnelService.dbo.pors_orderitem.DeliveryDate                  as DeliveryDate,
       PersonnelService.dbo.pors_orderitem.DeliveryBuilding as DeliveryBuilding,
       PersonnelService.dbo.pors_orderitem.DeliveryFloor as DeliveryFloor,
       Sum(PersonnelService.dbo.pors_orderitem.quantity * PersonnelService
           .dbo.pors_orderitem
           .priceperone) AS
                                                                            TotalPrice,
       s.amount                                                          AS
                                                                            SubsidyCap,
       CASE
           WHEN (Sum(quantity * priceperone) - s.amount) < 0 THEN 0
           ELSE (Sum(quantity * priceperone) - s.amount)
           END                                                           AS
                                                                            PersonnelDebt,
       CASE
           WHEN s.amount - Sum(PersonnelService.dbo.pors_orderitem.quantity *
                               PersonnelService.dbo.pors_orderitem.priceperone) < 0 THEN s.Amount
           ELSE Sum(PersonnelService.dbo.pors_orderitem.quantity * PersonnelService.dbo.pors_orderitem.priceperone)
           END                                                           AS SubsidySpent
FROM PersonnelService.dbo.pors_orderitem
         INNER JOIN PersonnelService.dbo.pors_subsidy AS s
                    ON PersonnelService.dbo.pors_orderitem.deliverydate BETWEEN s.fromdate AND
                        COALESCE(s.untildate,
                                 N'1499/12/12')
         LEFT JOIN HR.dbo.Users on HR.dbo.Users.UserName = PersonnelService.dbo.pors_orderitem.Personnel

GROUP BY PersonnelService.dbo.pors_orderitem.personnel,
         PersonnelService.dbo.pors_orderitem.deliverydate,
         s.amount,
         HR.dbo.Users.FirstName,
         HR.dbo.Users.LastName,
         PersonnelService.dbo.pors_orderitem.DeliveryBuilding,
         PersonnelService.dbo.pors_orderitem.DeliveryFloor,
         HR.dbo.Users.NationalCode
