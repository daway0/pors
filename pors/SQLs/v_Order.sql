SELECT Row_number()                                                                                           OVER (ORDER BY PersonnelService.dbo.pors_orderitem.deliverydate) AS Id, Users.NationalCode,
       Users.FirstName,
       Users.LastName,
       PersonnelService.dbo.pors_orderitem.Personnel                                                       AS Personnel,
       PersonnelService.dbo.pors_orderitem.DeliveryDate                                                    AS DeliveryDate,
       PersonnelService.dbo.pors_orderitem.DeliveryBuilding                                                AS DeliveryBuilding,
       PersonnelService.dbo.pors_orderitem.DeliveryFloor                                                   AS DeliveryFloor,
       dbp.Caption                                                                                         AS DeliveryBuildingPersian,
       dfp.Caption                                                                                         AS DeliveryFloorPersian,
       Sum(PersonnelService.dbo.pors_orderitem.quantity *
           PersonnelService.dbo.pors_orderitem.priceperone)                                                AS TotalPrice,
       s.amount                                                                                            AS SubsidyCap,
       CASE
           WHEN (Sum(quantity * priceperone) - s.amount)
               < 0 THEN 0
           ELSE (Sum(quantity * priceperone) - s.amount) END                                               AS PersonnelDebt,
       CASE
           WHEN s.amount -
                Sum(PersonnelService.dbo.pors_orderitem.quantity * PersonnelService.dbo.pors_orderitem.priceperone)
               < 0 THEN s.Amount
           ELSE Sum(PersonnelService.dbo.pors_orderitem.quantity *
                    PersonnelService.dbo.pors_orderitem.priceperone) END                                   AS SubsidySpent
FROM PersonnelService.dbo.pors_orderitem
         INNER JOIN
     PersonnelService.dbo.pors_subsidy AS s
     ON PersonnelService.dbo.pors_orderitem.deliverydate BETWEEN s.fromdate AND COALESCE(s.untildate, N'1499/12/12')
         LEFT JOIN
     Users ON Users.UserName = PersonnelService.dbo.pors_orderitem.Personnel
         INNER JOIN
     HR_constvalue AS dbp ON dbp.Code = PersonnelService.dbo.pors_orderitem.DeliveryBuilding
         INNER JOIN
     HR_constvalue AS dfp ON dfp.Code = PersonnelService.dbo.pors_orderitem.DeliveryFloor
GROUP BY PersonnelService.dbo.pors_orderitem.personnel, PersonnelService.dbo.pors_orderitem.deliverydate, s.amount,
         Users.FirstName, Users.LastName, PersonnelService.dbo.pors_orderitem.DeliveryBuilding,
         PersonnelService.dbo.pors_orderitem.DeliveryFloor, Users.NationalCode, dbp.Caption, dfp.Caption