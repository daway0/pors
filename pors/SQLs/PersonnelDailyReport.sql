SELECT row_number() over (order by (select null)) as Id,
           orders.Personnel,
           users.FirstName,
           users.LastName,
           team.TeamName,
           role.RoleName,
           item.ItemName,
           orders.Quantity,
           orders.DeliveryDate
    FROM pors_orderitem AS orders
             INNER JOIN hr.dbo.userteamrole AS teamrole
                        ON teamrole.username = orders.personnel
             INNER JOIN pors_item AS item
                        ON orders.item_id = item.id
             INNER JOIN hr.dbo.users AS users
                        ON users.username = orders.personnel
             INNER JOIN hr.dbo.team AS team
                        ON teamrole.teamcode = team.teamcode
             INNER JOIN hr.dbo.role AS role
                        ON role.roleid = teamrole.roleid