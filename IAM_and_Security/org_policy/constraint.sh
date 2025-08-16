gcloud org-policies set-custom-constraint constraint.yaml # make the custom constraint available for org policies
gcloud org-policies set-policy policy.yaml # apply new constraint

## To remove constraint, run gcloud org-policies reset custom.gcsBucketLocationConstraint --project PROJECT_ID (with your project id)