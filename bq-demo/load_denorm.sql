SELECT
  *
FROM
  customer c
LEFT JOIN
  ORDER o
ON
  c.id = o.cid
LEFT JOIN
  line_iems AS li
ON
  o.id = li.oid
left JOIN
  products as p
on li.id = p.liid