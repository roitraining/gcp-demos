# create the initial time travel table
bq query \
--use_legacy_sql=false \
--destination_table=class.time_travel \
--replace \
'SELECT
  c.*,
  o.order_num,
  o.order_date,
  FORMAT_DATETIME("%B", DATETIME(order_date)) AS month
FROM
  `roi-bq-demos.bq_demo_small.customer` c
JOIN
  `roi-bq-demos.bq_demo_small.order` o
ON
  c.cust_id = o.cust_id
WHERE
  cust_state = "CA"
  AND order_date BETWEEN "2018-01-01"
  AND "2018-01-31"'

# grab the time of completion for the table update
export TARGET=$(date +"%s")

bq query \
--use_legacy_sql=false \
--destination_table=class.time_travel \
--append_table \
'SELECT
  c.*,
  o.order_num,
  o.order_date,
  FORMAT_DATETIME("%B", DATETIME(order_date)) AS month
FROM
  `roi-bq-demos.bq_demo_small.customer` c
JOIN
  `roi-bq-demos.bq_demo_small.order` o
ON
  c.cust_id = o.cust_id
WHERE
  cust_state = "CA"
  AND order_date BETWEEN "2018-02-01"
  AND "2018-02-28"'
  
echo "Your time travel table is ready!"
echo "Your time travel target is $TARGET"