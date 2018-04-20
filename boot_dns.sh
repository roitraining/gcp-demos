 #!/bin/bash

# startup script to register a DNS name for GCE VM
# assumes that zone and domain are set in metadata
# fails if already exists - should test and remove if already there
EXT_IP=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" -H "Metadata-Flavor: Google")
DNS_ZONE=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/dns-zone" -H "Metadata-Flavor: Google")
DNS_DOMAIN=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/domain" -H "Metadata-Flavor: Google")
HOST_NAME=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google")
gcloud dns record-sets transaction start --zone=$DNS_ZONE
gcloud dns record-sets transaction add --zone=$DNS_ZONE --name=$HOST_NAME.$DNS_DOMAIN --type=A --ttl=300 $EXT_IP
gcloud dns record-sets transaction execute --zone=$DNS_ZONE