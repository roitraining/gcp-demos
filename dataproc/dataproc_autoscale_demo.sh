# run in cloud shell to create the demo cluster with autoscaling enabled
# This version uses autoscaling for secondary workers instead of manual scaling

# create the autoscaling policy
gcloud dataproc autoscaling-policies import autoscaling_demo_policy \
    --region=us-central1 \
    --source="./autoscaling_policy.yaml"


# create the autoscaling cluster
gcloud dataproc clusters create demo-cluster-autoscale \
    --region us-central1 \
    --zone us-central1-a \
    --worker-machine-type=n1-standard-8 \
    --num-workers=2 \
    --autoscaling-policy=autoscaling_demo_policy \
    --secondary-worker-type=spot \
    --secondary-worker-machine-types=type=n1-standard-8 \
    --secondary-worker-boot-disk-size=30 \
    --verbosity=error

# run in cloud shell to submit a job to the cluster
# The cluster will automatically scale secondary workers based on job demand
export PROJECT_ID=$(gcloud config get-value project)
gsutil mb gs://$PROJECT_ID
gcloud dataproc jobs submit hadoop \
    --cluster=demo-cluster-autoscale \
    --region=us-central1 \
    --class=org.apache.hadoop.examples.terasort.TeraGen \
    --jars=file:///usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar \
    -- -D mapreduce.job.maps=800 10000000000 gs://$PROJECT_ID/tg_n/$(date +%s)

# delete the cluster
gcloud dataproc clusters delete demo-cluster-autoscale \
    --region us-central1
