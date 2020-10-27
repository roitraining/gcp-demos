export PROJECT_ID=$(gcloud config get-value project)
gsutil mb gs://$PROJECT_ID
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar teragen -D mapreduce.job.maps=800 10000000000 gs://$PROJECT_ID/tg_n/$(date +%s)
