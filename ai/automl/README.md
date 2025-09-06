# AutoML demos

## Adoption Demo

## Forecasting Demo

This demo shows building a liquor sales forecasting model using AutoML and
tabular data.

### Outline

1. Initialize values and services
2. Create the dataset
3. Create and run model training job (creates model)
4. Make batch predictions
5. Create a Looker Studio dashboard to show prediction results

### Timing issues

1. Training the model takes 1.5-2 hours to complete, so waiting for the job to complete is generally not feasible
2. Doing batch prediction takes 25-30 minutes, so again, not feasible

### Workarounds




To use...

1. Click on the **automl_forecasting** notebook
2. Click the link to open in the console using Colab Enterprise
3. Replace the project ID placeholder with the correct value
4. Run the cells in the **Setting up** section
   1. Skip the cell that deletes/creates the BigQuery dataset if you have already run predictions and want to use the results already in BigQuery
5. If you haven't created the dataset and the model previously, run the cells in the **Creating the model** section.
   1. This takes a couple hours to run, so you might want to have a version of the dataset and model already created before class and just show the students
6. If you have the dataset and model already created, you can then run the cell in the **Using an existing model** section to get a reference to the existing model
7. Run the cells in the **Making predictions** section to do batch inference with the model
   1. This sadly takes like 25-30 minutes
   2. You might want to have already run the batch prior to class and skip actually running the inference here
8. Run the cells in the **Creating a dashboard** section and then demo the dashboard and results
9.  Run the cell in the **Cleaning up** section
