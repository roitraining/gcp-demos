import os
import apache_beam as beam
import random
import datetime

from apache_beam.io import ReadFromText

NUM_PRODUCTS = 10000
NUM_CUSTOMERS = 100000000
NUM_ORDERS = 200

states = ("AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL",\
"GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",\
"MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",\
"NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",\
"SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",\
"WY", "DC")

# basic config stuff
PROJECT = os.environ['DEVSHELL_PROJECT_ID']
BUCKET = "{}-bq-demo".format(PROJECT)


# def make_orders(cust_id):
def make_orders(customer):
    cust_id = customer.split(",")[0]
    for order_num in range(1, NUM_ORDERS+1):
        order_date = str(datetime.date(2018,random.randint(1,12),random.randint(1,28)))
        order_num = "{}-{}".format(cust_id, order_num)
        row = [order_num, str(cust_id), order_date]
        yield ",".join(row)

def make_lines(order_string):
    order = order_string.split(",")
    for line_item_num in range(1,11):
        order_num = order[0]
        line_item_num = str(line_item_num)
        prod_code = str(random.randint(0,NUM_PRODUCTS))
        qty = str(random.randint(0,10))
        row = [order_num, line_item_num, prod_code, qty]
        yield ",".join(row)

def create_cust_ids(num_cust_ids):
    for cust_id in range(0,num_cust_ids):
        yield cust_id

def make_customer(cust_id):
    cust_num = str(cust_id)
    cust_name = "Customer_" + cust_num + "_Name"
    phone = str(random.randint(100,999))\
        + "-" + str(random.randint(100,999))\
        + "-" + str(random.randint(0,9999))
    cust_email = "Customer_" + cust_num + "_Email@{}.com".format(cust_name)
    cust_address = cust_num + " Main St."
    cust_state = states[random.randint(0,50)]
    cust_zip = str(random.randint(0,99999))
    row = [cust_num, cust_name, cust_address, cust_state, cust_zip, cust_email, phone]   
    return ",".join(row)

def create_pids(num_pids):
    for pid in range(0,num_pids):
        yield pid

def make_product(pid):
    prod_code = str(pid)
    prod_name = "Product {}".format(prod_code)
    prod_desc = "The product that's perfect for {} stuff".format(prod_code)
    prod_price = str(random.randint(0,50) * pid)
    row = [prod_code, prod_name, prod_desc, prod_price]   
    return ",".join(row)

def run():

    argv = []
    p1 = beam.Pipeline(argv = argv)

    # create the customer ids
    num_customers = p1 | "num_customers" >> beam.Create([NUM_CUSTOMERS])
    cust_ids = num_customers | beam.FlatMap(create_cust_ids)

    # create the product ids
    num_products = p1 | "num_product" >> beam.Create([NUM_PRODUCTS])
    pids = num_products | beam.FlatMap(create_pids)

    # create customers and products
    customers = cust_ids | "generate customer row" >> beam.Map(make_customer)
    products = pids | "generate product row" >> beam.Map(make_product)

    # output customer
    output = customers | "write customers to gcs" >> beam.io.WriteToText("gs://{}/customer".format(BUCKET))

    # output products
    output = products | "write products to gcs" >> beam.io.WriteToText("gs://{}/product".format(BUCKET))

    p1.run().wait_until_finish()

    argv = [
        '--project={0}'.format(PROJECT),
        '--job_name=bq-demo-data-{}'.format(
            datetime.datetime.now().strftime('%Y%m%d%H%M%S')),
        '--save_main_session',
        '--staging_location=gs://{0}/staging/'.format(BUCKET),
        '--temp_location=gs://{0}/temp/'.format(BUCKET),
        '--runner=DataflowRunner',
        '--worker_machine_type=n1-standard-8',
        '--region=us-central1',
    ]

    p2 = beam.Pipeline(argv = argv)    

    customers = p2 | 'read c' >> ReadFromText('gs://{}/customer*'.format(BUCKET))
    orders = customers | beam.FlatMap(make_orders)
    line_items = orders | beam.FlatMap(make_lines)
 
    # output orders
    output = orders | "write orders to gcs" >> beam.io.WriteToText("gs://{}/order".format(BUCKET))

    # output line items
    output = line_items | "write line_items to gcs" >> beam.io.WriteToText("gs://{}/line_items".format(BUCKET))

    p2.run() 

if __name__ == '__main__':
   run()
