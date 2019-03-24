import os
import apache_beam as beam
import random
import datetime

NUM_PRODUCTS = 10000
NUM_CUSTOMERS = 1000000
NUM_ORDERS = 100

states = ("AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL",\
"GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",\
"MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",\
"NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",\
"SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",\
"WY", "DC")

# basic config stuff
PROJECT = os.environ['DEVSHELL_PROJECT_ID']
BUCKET = "{}-df".format(PROJECT)

argv = [
    '--project={0}'.format(PROJECT),
    '--job_name=shq-demo-data-{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S')),
    '--save_main_session',
    '--staging_location=gs://{0}/staging/'.format(BUCKET),
    '--temp_location=gs://{0}/temp/'.format(BUCKET),
    # '--requirements_file=dflow-req.txt',
    '--runner=DataflowRunner',
    '--num_workers=10',
    '--machine_type=n1-standard-4'
]

def make_orders(cid):
    for order_num in range(1, NUM_ORDERS+1):
        orderDate = str(datetime.date(2018,random.randint(1,12),random.randint(1,28)))
        o_num = "{}-{}".format(cid, order_num)
        row = [o_num, str(cid), orderDate]
        yield ",".join(row)

def make_lines(order_string):
    order = order_string.split(",")
    for line_number in range(1,11):
        oline_order_num = order[0]
        oline_line_item_num = str(line_number)
        oline_prod_code = str(random.randint(0,NUM_PRODUCTS))
        oline_qty = str(random.randint(0,10))
        row = [oline_order_num, oline_line_item_num, oline_prod_code, oline_qty]
        # yield ""
        yield ",".join(row)

def create_cids(num_cids):
    for cid in range(0,num_cids):
        yield cid

def make_customer(cid):
    custNum = str(cid)
    custName = "Customer_" + custNum + "_Name"
    phone = str(random.randint(100,999))\
        + "-" + str(random.randint(100,999))\
        + "-" + str(random.randint(0,9999))
    email = "Customer_" + custNum + "_Email@{}.com".format(custName)
    address = custNum + " Main St."
    state = states[random.randint(0,50)]
    zipCode = str(random.randint(0,99999))
    row = [custNum, custName, address, state, zipCode, email, phone]   
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

    p = beam.Pipeline(argv = argv)

    # create the customer ids
    num_customers = p | "num_customers" >> beam.Create([NUM_CUSTOMERS])
    cids = num_customers | beam.FlatMap(create_cids)

    # create the product ids
    num_products = p | "num_product" >> beam.Create([NUM_PRODUCTS])
    pids = num_products | beam.FlatMap(create_pids)
    customers = cids | "generate customer row" >> beam.Map(make_customer)
    products = pids | "generate product row" >> beam.Map(make_product)
    orders = cids | beam.FlatMap(make_orders)
    line_items = orders | beam.FlatMap(make_lines)

    # output customer
    output = customers | "write customers to gcs" >> beam.io.WriteToText("gs://jwd-gcp-demos-df/customers")

    # output orders
    output = orders | "write orders to gcs" >> beam.io.WriteToText("gs://jwd-gcp-demos-df/orders")

    # output line items
    output = line_items | "write line_items to gcs" >> beam.io.WriteToText("gs://jwd-gcp-demos-df/line_items")

    # output products
    output = products | "write products to gcs" >> beam.io.WriteToText("gs://jwd-gcp-demos-df/products")

    p.run()

if __name__ == '__main__':
   run()
