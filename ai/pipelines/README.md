# Simple Vertex AI Pipeline demo

## Setup
1. Load [notebook](https://github.com/roitraining/challenge-labs-public/blob/main/data%20science/challenge-labs-pipelines.ipynb) in a Vertex AI Workbench instance
   1. You can rull in Collab Enterprise, but you need to change `serviceAccount:` to `user:` as the code will run as you rather than the service account of an instance VM.

## Demo

1. Run all the cells in the notebook
2. Talk the students through the pipeline definition
3. Show the students where the source data is
4. Show the students the pipeline graph and discuss the nodes
5. Show the students the dataset and the endpoint created
6. Discuss the compilation and job submission steps
7. Highlight that the actual training will take 2+hours
8. You can always do a pipeline execution ahead of time to show results

## Teardown

1. Manually undeploy the model from the endpoint
2. Delete the endpoint
3. Optionally, delete the model and the dataset