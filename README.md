# ROI GCP Training Demos

## Setup
* Open Cloud Shell
* Run the following to clone the repo and change directories
```
cd ~
git clone https://github.com/roitraining/gcp-demos.git
cd gcp-demos
```

## BQ Demo
The goal of this demo is to show the price/performance impact of different data structures and BQ features. You will run a query that generates identical results against multiple copies of data that's organized in different ways, and highlight how price/performance differs.

See separate [README.md](https://github.com/roitraining/gcp-demos/blob/master/bq-demo/README.md)

## Misc Data Demos
### Sum Array
This demo was created in response to a student asking about how to sum array columns. It shows:
* Shows how to show rows with array and sum of array using subquery
* Shows how to show rows with array and sum of array using cross join and agg
* Shows how to generate a denormalized view of a table with an array column
* Shows how to query denormalized view and show array col and sum

To use:
* Open ```sum_array.sql```
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

### Hackernews BQ demo
The purpose of this demo is to provide step-by-step breakdown of structs, windowing functions, and arrays. It's intended as an alternative to the code in the class.
* Open ```hackernews_demo.sql```
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

### Github BQ demo
The purpose of this demo is to provide step-by-step breakdown of searching by array length, more struct creation, correlated cross-joins with UNNEST statement, and querying on values within a repeated struct.
* Open ```github_demo.sql```
* Copy/paste queries one at a time and show results
* For each result, show the JSON code to clarify

### Dataproc scaling and pre-emptable instances
* Open ```dataproc_scale_demo.sh```
* Use first command in Cloud Shell to create the cluster
* Use second set of commands in cloud Shell to submit the job
* Show the slow progress of the job
* Open a 2nd Cloud Shell session, and use the third command to add nodes to
  the cluster, changing the number of nodes to fit within your quotas.
* Show the new nodes. Show the improved rate of progress
* Run the last command to tear down the cluster

### Approximation functions
This demo shows the performance/accuracy tradeoff of using approxmiation
function vs accurate function.
* Open ```approx.sql``` 
* Copy/paste queries one at a time, executing in Qwiklabs project
* Show difference between answers and query times
* In a test run, I approx taking 11% as long and being within 0.32%

## Arch Demos
### Cloud Functions Demo
This demonstrates creation of a Cloud Function that monitors additions to a
bucket, and will check the picture for offensive content, and blur the picture
if needed.
* ```. ./gcf-demo-setup.sh``` to deploy the cloud function
* Discuss purpose (function finds offensive images and replaces with blurred images)
* Show the students the zombie picture (either whole picture or thumbnail)
* Upload zombie photo into the "originals" bucket in your project
* Show students logs with GCF info
* Show students blurred image in the "blurred" bucket
