select
	pi2.*,
	ip.title as itemProvider,
	pc2.CategoryName,
	case
		when pf.[Type] = 'L' then 1
		else 0
	end as IsLiked,
	case
		when pf.[Type] = 'D' then 1
		else 0
	end as IsDissLiked,
	COALESCE(ppc.hasComment, 0) as IsCommented,
	if2.TotalLikes,
	if2.TotalDissLikes,
	if2.TotalComments
from
	pors_item pi2
left join pors_feedback pf 
on
	pf.Item_id = pi2.id
	and pf.User_id = %s
left join (
	select
		Item_id,
		User_id,
		CASE
			when count(*) > 0 then 1
		END as hasComment
	from
		pors_comment pc
	group by
		Item_id,
		User_id
) ppc on
	ppc.Item_id = pi2.id
	and ppc.User_id = %s
inner join pors_category pc2 on
	pc2.id = pi2.Category_id
inner join ItemFeedbacks if2 on
	if2.Item = pi2.id
inner join pors_itemprovider ip on
	ip.id = pi2.ItemProvider_id 