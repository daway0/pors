select Personnel,
       DeliveryDate,
       sum(Quantity * PricePerOne)              TotalPrice,
       s.Amount                                 SubsidyAmount,
       CASE WHEN (SUM(Quantity * PricePerOne) - s.Amount) < 0 THEN 0
         ELSE (SUM(Quantity * PricePerOne) - s.Amount)
    END AS PersonnelDebt

from pors_orderitem
         inner join pors_subsidy s on DeliveryDate BETWEEN s.FromDate and COALESCE(s.UntilDate, '1499/12/12')
group by Personnel, DeliveryDate, s.Amount