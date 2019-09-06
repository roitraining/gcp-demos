 #!/bin/bash

# enable apis
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable vision.googleapis.com

# create bucket
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID-cf-originals
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID-cf-blurred

# do a clean install of repo
cd ~
rm -rf ~/nodejs-docs-samples
git clone https://github.com/GoogleCloudPlatform/nodejs-docs-samples.git

# deploy the function
cd functions/imagemagick/
gcloud functions deploy blurOffensiveImages --trigger-bucket=$DEVSHELL_PROJECT_ID-cf-originals --set-env-vars BLURRED_BUCKET_NAME=gs://$DEVSHELL_PROJECT_ID-cf-blurred
# change back to demos directory
cd ~/gcp-demos
