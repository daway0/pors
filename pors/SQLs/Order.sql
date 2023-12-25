WITH summary AS (SELECT username,
                        teamcode,
                        roleid,
                        ROW_NUMBER() OVER(PARTITION BY username order by roleid desc) AS roww
                 FROM HR.dbo.UserTeamRole p)
SELECT Row_number()                                                         OVER (ORDER BY PersonnelService.dbo.pors_orderitem.deliverydate) AS Id, HR.dbo.Users.FirstName,
       HR.dbo.Users.LastName,
       PersonnelService.dbo.pors_orderitem.Personnel                     as Personnel,
       TeamName,
       RoleName,
       PersonnelService.dbo.pors_orderitem.DeliveryDate                  as DeliveryDate,
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
         LEFT JOIN (SELECT *
                    FROM summary
                    WHERE roww = 1) AS teamrole
                   ON teamrole.username = pors_orderitem.Personnel
         LEFT JOIN HR.dbo.team AS team
                   ON teamrole.teamcode = team.teamcode
         LEFT JOIN HR.dbo.role AS role
                   ON role.roleid = teamrole.roleid
GROUP BY PersonnelService.dbo.pors_orderitem.personnel,
         PersonnelService.dbo.pors_orderitem.deliverydate,
         s.amount,
         HR.dbo.Users.FirstName,
         HR.dbo.Users.LastName,
         TeamName,
         RoleName