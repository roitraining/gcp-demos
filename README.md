# ROI GCP Training Demos

## Setup
* Open Cloud Shell
* Run the following to clone the repo and change directories
```
cd ~
git clone https://github.com/roitraining/gcp-demos.git
cd gcp-demos
```

## Misc Data Demos

### BigQuery Demos
* Check out <https://roitraining.github.io/gcp-demos/#1> for details on 
  demoing or using **Do-It-Now** activities

### Dataproc scaling and pre-emptable instances
* Open ```dataproc_scale_demo.sh```
* Use first command in Cloud Shell to create the cluster
* Use second set of commands in cloud Shell to submit the job
* Show the slow progress of the job
* Open a 2nd Cloud Shell session, and use the third command to add nodes to
  the cluster, changing the number of nodes to fit within your quotas.
* Show the new nodes. Show the improved rate of progress
* Run the last command to tear down the cluster

### DLP
* Open application at <https://roi-gcp-demos.appspot.com/dlp_demo>
* Enter text with no sensitive data into left pane; see results on right
* Enter sensitive data in left pane; see results on right
* Fiddle around with contextual info on left, see ratings change on right
* Demonstrate different remediation tactics with blue buttons
* Optional - show source code to class


### Dataflow streaming in Python
* See <https://github.com/roitraining/gcp-demos/tree/master/dflow-bq-stream-python>

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