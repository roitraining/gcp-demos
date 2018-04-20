#!/bin/bash
#ssh into master and run this
#add 100 premptible nodes and watch throughput go up

 hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar teragen -D mapreduce.job.maps=800 10000000000 gs://jwd-gcp-demos/tg_n/