SELECT Row_number()
               OVER (
                   ORDER BY dbo.pors_orderitem.deliverydate)             AS Id,
       hr.dbo.Users.FirstName,
       hr.dbo.Users.LastName,
       dbo.pors_orderitem.Personnel                                      as Personnel,
       dbo.pors_orderitem.DeliveryDate                                   as DeliveryDate,
       dbo.PersianToMiladi(dbo.pors_orderitem.deliverydate)              AS MiladiDeliverydate,
       dbo.CheckEligibilityFunction(
               dbo.PersianToMiladi(dbo.pors_orderitem.deliverydate), 'BRF'
       )                                                                 AS openForBreakfast,
       dbo.CheckEligibilityFunction(
               dbo.PersianToMiladi(dbo.pors_orderitem.deliverydate), 'LNC'
       )                                                                 AS openForLaunch,
       Sum(dbo.pors_orderitem.quantity * dbo.pors_orderitem.priceperone) AS
                                                                            TotalPrice,
       s.amount                                                          AS
                                                                            SubsidyCap,
       CASE
           WHEN (Sum(quantity * priceperone) - s.amount) < 0 THEN 0
           ELSE (Sum(quantity * priceperone) - s.amount)
           END                                                           AS
                                                                            PersonnelDebt,
       CASE
           WHEN s.amount - Sum(dbo.pors_orderitem.quantity * dbo.pors_orderitem.priceperone) < 0 THEN s.Amount
           ELSE Sum(dbo.pors_orderitem.quantity * dbo.pors_orderitem.priceperone)
           END                                                           AS SubsidySpent

FROM dbo.pors_orderitem
         INNER JOIN dbo.pors_subsidy AS s
                    ON dbo.pors_orderitem.deliverydate BETWEEN s.fromdate AND
                        COALESCE(s.untildate,
                                 N'1499/12/12')
         LEFT JOIN HR.dbo.Users on HR.dbo.Users.UserName = dbo.pors_orderitem.Personnel
GROUP BY dbo.pors_orderitem.personnel,
         dbo.pors_orderitem.deliverydate,
         s.amount,
         hr.dbo.Users.FirstName,
         hr.dbo.Users.LastName