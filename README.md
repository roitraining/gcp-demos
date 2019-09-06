# ROI GCP Training Demos

## Setup
* Open Cloud Shell
* Run the following to clone the repo and change directories
```
cd ~
git clone https://github.com/roitraining/gcp-demos.git
cd gcp-demos
```

## Dataproc scaling and pre-emptable instances
* Create a dataproc cluster with 2 nodes in a region where you have a lot of CPU/Disk quota
* SSH into master and run the command from ```dataproc_scale_demo.sh```
* Note progress (or lack thereof)
* Add hundreds of CPUs of preemptable instances
* Go back to master SSH window and show uptick in performance

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
* Upload zombie photo into the "originals" bucket in your project
* Show students logs with GCF info
* Show students blurred image in the "blurred" bucket

## Misc
* startup script that registers dns record
* queries from Data Engineering course slides
* wikimedia demo query
