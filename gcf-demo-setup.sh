 #!/bin/bash

# enable apis
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable vision.googleapis.com

# create bucket
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID-files

# do a clean install of repo
cd ~
rm -rf ~/nodejs-docs-samples
git clone https://github.com/GoogleCloudPlatform/nodejs-docs-samples.git

# change to a commit where the demo works
cd nodejs-docs-samples
git checkout 5e4a52da38779ba2546fc1e05cd228474b669c6b

# deploy the function
cd functions/imagemagick/
gcloud functions deploy blurOffensiveImages --trigger-bucket=$DEVSHELL_PROJECT_ID-files

# change back to demos directory
cd ~/gcp-demos
