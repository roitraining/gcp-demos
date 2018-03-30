with s0 as
(SELECT
  inv.invoice_num as invoice_num,
  inv.date as date,
  c.name as customer,
  s.name as salesperson,
  li.*
FROM
  bq_perf.line_items li
LEFT JOIN
  bq_perf.invoices inv
ON
  inv.invoice_num = li.invoice
LEFT JOIN
  bq_perf.customers c
ON
  c.id = inv.customer
LEFT JOIN
  bq_perf.salespeople s
ON
  s.id = inv.salesperson
WHERE
  salesperson = "sales-0")

SELECT
  invoice,
  date,
  customer,
  salesperson,
  SUM(line_total)
FROM
  bq_perf.denorm
WHERE
  salesperson = "Mrs. 0"
GROUP BY
  invoice,
  date,
  customer,
  salesperson

SELECT
  invoice,
  date,
  customer,
  salesperson,
  SUM(li.line_total)
FROM
  bq_perf.semi_denorm,
  unnest(line_items) as li
WHERE
  salesperson = "Mrs. 0"
GROUP BY
  invoice,
  date,
  customer,
  salesperson

