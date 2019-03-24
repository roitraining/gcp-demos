# ROI GCP Training Demos

## Setup
* Open Cloud Shell
* Run the following to clone the repo and change directories
```
cd ~
git clone https://github.com/roitraining/gcp-demos.git
cd gcp-demos
```

## Dataproc scaling and preµemtable instances
* Create a dataproc cluster with 2 nodes in a region where you have a lot of CPU/Disk quota
* SSH into master and run the command from ```dataproc_scale_demo.sh```
* Note progress (or lack thereof)
* Add hundreds of CPUs of preemptable instances
* Go back to master SSH window and show uptick in performance

Credit to Nigel for this demo

## Hackernews BQ demo

The purpose of this demo is to provide step-by-step breakdown of structs, windowing functions, and arrays. It's intended as an alternative to the code in the class.

* Open ```hackernews_demo.sql```
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

## Github BQ demo

The purpose of this demo is to provide step-by-step breakdown of searching by array length, more struct creation, and correlated cross-joins with UNNEST statement

* Open ```github_demo.sql```
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

## Cloud Functions Demo

* ```. ./gcf-demo-setup.sh``` to deploy the cloud function
* Discuss purpose (function finds offensive images and replaces with blurred images)
* Show the students the zombie picture (either whole picture or thumbnail)
* Upload zombie photo
* Show students logs with GCF info
* Show students blurred image

## BQ Demo
The goal of this demo is to show the price/performance impact of different data structures and BQ features. You will run a query that generates identical results against multiple copies of data that's organized in different ways, and highlight how price/performance differs.

The data is sample order data with:
* Customers
* Orders
* Line items
* Products

There are several versions of the data store:
* Normalized, relational
* Fully denormalized
* Single level nesting
    * Order as parent row
    * Customer data denormalized into order rows
    * Line items aggregated into an array
    * Product data denormalized into line item structs
* Double level nesting
    * Customer as parent row
    * Orders aggregated into an array
    * Line items aggregated into an array for each order
    * Product data denormalized into line item structs
* Single level nested, partitioned by order date
* Single level nested, partitioned by order date, clustered by zip code

The query you'll benchmark is looking to return:
* Total sizes
* In March 2018
* Summed by zip code

### To demo
* Run the query saved in ```norm-query.sql```
    * Highlight the time taken
    * Highlight the data processed
* Run the query saved in ```denorm-query.sql```
    * Highlight the time taken and speak about importance of diff
    * Highlight the data processed and speak about importance of diff
* Run the query saved in ```nested-once.sql```
    * Highlight the time taken and speak about importance of diff
    * Highlight the data processed and speak about importance of diff
    * Talk about complexity of query
* Run the query saved in ```nested-twice.sql```
    * Highlight the time taken and speak about importance of diff
    * Highlight the data processed and speak about importance of diff
    * Talk about complexity of query
* Run the query saved in ```nested-partitioned.sql```
    * Highlight the time taken and speak about importance of diff
    * Highlight the data processed and speak about importance of diff
* Run the query saved in ```nested-clustered.sql```
    * Highlight the time taken and speak about importance of diff
    * Highlight the data processed and speak about importance of diff

### Other interesting stuff
* We created the normalized dataset first, then generated then derived the other tables using queries and saving results to permanent tables
    * ```load_denorm.sql ``` generates the fully denormalized table
    * ```load_nested_once.sql``` generates the table with line items nested in orders
    ```load_nested_twice.sql``` generates the table with orders nested in customer and line items nested in orders

* To generate the partitioned and clustered tables, we used the ```bq``` command line. You can see the specific commands in the ```misc.txt``` file.


## Misc
* startup script that registers dns record
* queries from Data Engineering course slides
* wikimedia demo query
