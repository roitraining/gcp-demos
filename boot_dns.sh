gcloud dns record-sets transaction add --zone=$DNS_ZONE --name=$HOST_NAME.$DNS_DOMAIN --type=A --ttl=300 $EXT_IP
