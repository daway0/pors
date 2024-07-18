select ROW_NUMBER() over (order by (select null)) as id,
	pi2.id as Item,
	count(pf.id) as TotalLikes,
	count(pf2.id) as TotalDissLikes,
	count(pc.id) as TotalComments
from
	pors_item pi2
left join pors_feedback pf 
on
	pf.Item_id = pi2.id
	and pf.[Type] = 'L'
left join pors_feedback pf2 
on
	pf2.Item_id = pi2.id
	and pf2.[Type] = 'D'
left join pors_comment pc 
on
	pc.Item_id = pi2.id
GROUP By
	pi2.id;