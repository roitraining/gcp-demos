# ROI GCP Training Demos

## Normalized vs. denormalized queries for demoing perf difference
* Show norm.png and talk through schema
* Show schema in https://bigquery.cloud.google.com/dataset/jwd-gcp-demos:cpb200_liquor_sales?pli=1
* Copy/paste liquor_rel.sql into BQ UI and run query
* Highlight time and data processed
* Show denorm.png and talk through schema
* Show schema in https://bigquery.cloud.google.com/dataset/jwd-gcp-demos:cpb200_liquor_sales?pli=1
* Copy/paste liquor_denrom.sql in BQ UI and run query
* Highlight time and data processed

## Dataproc scaling and preµemtable instances
* Create a dataproc cluster with 2 nodes in a region where you have a lot of CPU/Disk quota
* SSH into master and run the command from dataproc_scale_demo.sh
* Note progress (or lack thereof)
* Add hundreds of CPUs of preemptable instances
* Go back to master SSH window and show uptick in performance

Credit to Nigel for this demo

## Hackernews BQ demo

The purpose of this demo is to provide step-by-step breakdown of structs, windowing functions, and arrays. It's intended as an alternative to the code in the class.

* Open hackernews_demo.sql
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

## Github BQ demo

The purpose of this demo is to provide step-by-step breakdown of searching by array length, more struct creation, and correlated cross-joins with UNNEST statement

* Open github_demo.sql
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

## Cloud Functions Demo

* Visit https://github.com/GoogleCloudPlatform/nodejs-docs-samples/tree/master/functions/imagemagick

## Misc
* startup script that registers dns record
* queries from Data Engineering course slides
* wikimedia demo query
