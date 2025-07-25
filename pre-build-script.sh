#!/usr/bin/env bash

set -euxo pipefail

# Prerequisites:
# - awk
# - jq
# - sed
# - skopeo
# - yq

echo "__________________________________________________ Building microshift-gitops.spec file"
# --- ARGO-CD variables ---
# Define the version and tag for the Argo CD image.
GITOPS_VERSION="1.16.1-1"
GITOPS_TAG="v"${GITOPS_VERSION}

# ARGO-CD variables
#GITOPS_VERSION="1.16"
#GITOPS_TAG="gitops-${GITOPS_VERSION}-rhel-9-candidate"
#GITOPS_ARGO_CD_PKG="openshift-gitops-argocd-rhel9-container"

# REDIS variables
REDIS_TAG="9.6-1753161831"
#REDIS_TAG="rhel-9.3.0-container-released"
#REDIS_PKG="redis-6-container"

# ARGOCD build steps
ARGO_CD_IMAGE_URL="registry.redhat.io/openshift-gitops-1/argocd-rhel9:${GITOPS_TAG}"
ARGO_CD_IMAGE_TAG="${GITOPS_VERSION}"

#ARGO_CD_IMAGE_URL=$(brew buildinfo ${ARGO_CD_LATEST_BUILD} | grep "Extra: " | sed -e 's/Extra: //g' | yq '.image.index.pull[0]')
#ARGO_CD_IMAGE_TAG=$(brew buildinfo ${ARGO_CD_LATEST_BUILD} | grep "Extra: " | sed -e 's/Extra: //g' | yq '.image.index.tags[0]')

# Get the SHA id for the respective processor architectures.
ARGO_CD_IMAGE_SHA_X86=$(skopeo inspect docker://${ARGO_CD_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="amd64") | .digest')
ARGO_CD_IMAGE_SHA_ARM=$(skopeo inspect docker://${ARGO_CD_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="arm64") | .digest')

# Update the vars to be replaced in spec.in template file.
sed -i "s/REPLACE_ARGO_CD_CONTAINER_SHA_X86/${ARGO_CD_IMAGE_SHA_X86}/g" microshift-gitops.spec.in
sed -i "s/REPLACE_ARGO_CD_CONTAINER_SHA_ARM/${ARGO_CD_IMAGE_SHA_ARM}/g" microshift-gitops.spec.in
sed -i "s/REPLACE_ARGO_CD_VERSION/${ARGO_CD_IMAGE_TAG}/g" microshift-gitops.spec.in

# Update spec file too, as the file generation from the template spec.in file is run prior to the pre-build-script execution.
sed -i "s/REPLACE_ARGO_CD_CONTAINER_SHA_X86/${ARGO_CD_IMAGE_SHA_X86}/g" microshift-gitops.spec
sed -i "s/REPLACE_ARGO_CD_CONTAINER_SHA_ARM/${ARGO_CD_IMAGE_SHA_ARM}/g" microshift-gitops.spec
sed -i "s/REPLACE_ARGO_CD_VERSION/${ARGO_CD_IMAGE_TAG}/g" microshift-gitops.spec

# REDIS build steps

# Find the latest build for the given tag and Redis-6 container package.
REDIS_IMAGE_URL="registry.redhat.io/rhel9/redis-6:${REDIS_TAG}"
#REDIS_LATEST_BUILD=$(brew latest-build ${REDIS_TAG} ${REDIS_PKG} --quiet | awk '{print $1}')

# Get the container image url.
#REDIS_IMAGE_URL=$(brew buildinfo ${REDIS_LATEST_BUILD} | grep "Extra: " | sed -e 's/Extra: //g' | yq '.image.index.pull[0]')

# Get the SHA id for the respective processor architectures.
REDIS_IMAGE_SHA_X86=$(skopeo inspect docker://${REDIS_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="amd64") | .digest')
REDIS_IMAGE_SHA_ARM=$(skopeo inspect docker://${REDIS_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="arm64") | .digest')

# Update the vars to be replaced in spec.in template file.
sed -i "s/REPLACE_REDIS_CONTAINER_SHA_X86/${REDIS_IMAGE_SHA_X86}/g" microshift-gitops.spec.in
sed -i "s/REPLACE_REDIS_CONTAINER_SHA_ARM/${REDIS_IMAGE_SHA_ARM}/g" microshift-gitops.spec.in

# Update spec file too, as the file generation from the template spec.in file is run prior to the pre-build-script execution.
sed -i "s/REPLACE_REDIS_CONTAINER_SHA_X86/${REDIS_IMAGE_SHA_X86}/g" microshift-gitops.spec
sed -i "s/REPLACE_REDIS_CONTAINER_SHA_ARM/${REDIS_IMAGE_SHA_ARM}/g" microshift-gitops.spec
