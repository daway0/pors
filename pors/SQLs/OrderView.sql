SELECT Row_number()
         OVER(
           ORDER BY dbo.pors_orderitem.deliverydate)                     AS Id,
       dbo.pors_orderitem.personnel,
       dbo.pors_orderitem.deliverydate,
       Sum(dbo.pors_orderitem.quantity * dbo.pors_orderitem.priceperone) AS
       TotalPrice,
       s.amount                                                          AS
       SubsidyAmount,
       CASE
         WHEN ( Sum(quantity * priceperone) - s.amount ) < 0 THEN 0
         ELSE ( Sum(quantity * priceperone) - s.amount )
       END                                                               AS
       PersonnelDebt
FROM   dbo.pors_orderitem
       INNER JOIN dbo.pors_subsidy AS s
               ON dbo.pors_orderitem.deliverydate BETWEEN s.fromdate AND
                                                          COALESCE (s.untildate,
                                                          N'1499/12/12')
GROUP  BY dbo.pors_orderitem.personnel,
          dbo.pors_orderitem.deliverydate,
          s.amount 