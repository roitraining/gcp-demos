# run in cloud shell to create the demo cluster
gcloud dataproc clusters create demo-cluster \
    --region us-central1 \
    --zone us-central1-a \
    --worker-machine-type=n1-standard-8 \
    --num-workers=2 \
    --num-secondary-workers=0 \
    --secondary-worker-boot-disk-size=30 \
    --delete-max-age=10m \
    --verbosity=error

# run in cloud shell to submit a job to the cluster
# show the progress rate (about 1% map per 30 seconds)
export PROJECT_ID=$(gcloud config get-value project)
gsutil mb gs://$PROJECT_ID
gcloud dataproc jobs submit hadoop \
    --cluster=demo-cluster \
    --region=us-central1 \
    --class=org.apache.hadoop.examples.terasort.TeraGen \
    --jars=file:///usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar \
    -- -D mapreduce.job.maps=800 10000000000 gs://$PROJECT_ID/tg_n/$(date +%s)

# run in cloud shell to add pre-emptible instances
# adjust the number of nodes to something within your quota
# show new progress rate (2-3%/sec)
gcloud dataproc clusters update demo-cluster \
    --num-secondary-workers 150 \
    --region us-central1

# delete the cluster
gcloud dataproc clusters delete demo-cluster \
    --region us-central1