#!/bin/bash -x

echo Starting Deployment

# Create the dojot namespace
kubectl create namespace dojot

kubectl create -f manifests/EXTERNAL_ACCESS/public-ip.yaml

# Create configuration files mappings
kubectl create -n dojot configmap iotagent-conf --from-file=iotagent/config.js
kubectl create -n dojot configmap kong-route-config --from-file=config_scripts/kong.config.sh
kubectl create -n dojot configmap create-admin-user --from-file=config_scripts/create-admin-user.sh

# Deploy Dojot services
kubectl create -f manifests/

echo Deployment is complete!
