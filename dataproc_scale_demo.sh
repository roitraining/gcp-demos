#!/bin/bash
read -p 'Bucket name: ' BUCKET

hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar teragen -D mapreduce.job.maps=800 10000000000 gs://$BUCKET/tg_n/$(date +%s)
