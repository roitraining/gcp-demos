select
    cust_num,
    cust_name,
    cust_address,
    cust_state,
    cust_zip,
    cust_email,
    cust_phone,
    array_agg(struct(
        o_num,
        o_cust_num,
        o_date,
        line_items
    )) as orders
from 
    `roi-bq-demo.bq_benchmark_tables_one_level_nest.table_nested`
group by
    cust_num,
    cust_name,
    cust_address,
    cust_state,
    cust_zip,
    cust_email,
    cust_phone