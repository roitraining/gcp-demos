 #!/bin/bash

bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.customer gs://$DEVSHELL_PROJECT_ID-bq-demo/customer* ./customer_schema.json
bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.order gs://$DEVSHELL_PROJECT_ID-bq-demo/order* ./order_schema.json
bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.product gs://$DEVSHELL_PROJECT_ID-bq-demo/product* ./product_schema.json
bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.line_item gs://$DEVSHELL_PROJECT_ID-bq-demo/line_item* ./line_item_schema.json
