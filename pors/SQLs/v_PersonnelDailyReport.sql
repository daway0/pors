WITH summary AS (SELECT username,
                        teamcode,
                        roleid,
                        ROW_NUMBER() OVER(PARTITION BY username order by roleid desc) AS roww
SELECT row_number() over (order by (select null)) as Id, orders.Personnel,
       users.FirstName,
       users.LastName,
       team.TeamName,
       role.RoleName,
       item.ItemName,
       item.id as   ItemId,
       orders.Quantity,
       orders.DeliveryDate
FROM PersonnelService.dbo.pors_orderitem AS orders
         INNER JOIN PersonnelService.dbo.pors_item AS item
                    ON orders.item_id = item.id
         LEFT JOIN (SELECT *
                    FROM summary
                    WHERE roww = 1) AS teamrole
                   ON teamrole.username = orders.personnel
         LEFT JOIN hr.dbo.users AS users
                   ON users.username = orders.personnel
         LEFT JOIN hr.dbo.team AS team
                   ON teamrole.teamcode = team.teamcode
         LEFT JOIN hr.dbo.role AS role
                   ON role.roleid = teamrole.roleid