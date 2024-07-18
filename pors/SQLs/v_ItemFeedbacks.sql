SELECT 
    ROW_NUMBER() OVER (ORDER BY pi2.id) AS id,
    pi2.id AS Item,
    COALESCE(likes.TotalLikes, 0) AS TotalLikes,
    COALESCE(dislikes.TotalDislikes, 0) AS TotalDisslikes,
    COALESCE(comments.TotalComments, 0) AS TotalComments
FROM 
    pors_item pi2
LEFT JOIN (
    SELECT Item_id, COUNT(*) AS TotalLikes
    FROM pors_feedback
    WHERE [Type] = 'L'
    GROUP BY Item_id
) likes ON likes.Item_id = pi2.id
LEFT JOIN (
    SELECT Item_id, COUNT(*) AS TotalDislikes
    FROM pors_feedback
    WHERE [Type] = 'D'
    GROUP BY Item_id
) dislikes ON dislikes.Item_id = pi2.id
LEFT JOIN (
    SELECT Item_id, COUNT(*) AS TotalComments
    FROM pors_comment
    GROUP BY Item_id
) comments ON comments.Item_id = pi2.id;