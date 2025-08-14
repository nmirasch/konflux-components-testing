#!/usr/bin/env bash

set -euxo pipefail

ARGO_CD_REPO="docker://registry.redhat.io/openshift-gitops-1/argocd-rhel9"
ARGO_CD_TAG_PATTERN="v1.16"

REDIS_REPO="docker://registry.redhat.io/rhel9/redis-6"
REDIS_TAG_PATTERN="9.6"

echo "Searching for latest Argo CD tag...using skopeo"

LATEST_ARGO_TAG=$(skopeo list-tags ${ARGO_CD_REPO} | jq -r '.Tags[]' | grep "^${ARGO_CD_TAG_PATTERN}" | grep -v -- "-source$" | sort -V | tail -n 1)
echo "Found latest Argo CD tag: ${LATEST_ARGO_TAG}"

echo "Searching for latest Redis tag..."

LATEST_REDIS_TAG=$(skopeo list-tags ${REDIS_REPO} | jq -r '.Tags[]' | grep "^${REDIS_TAG_PATTERN}" | grep -v -- "-source$" | sort -V | tail -n 1)
echo "Found latest Redis tag: ${LATEST_REDIS_TAG}"

ARGO_CD_IMAGE_URL="${ARGO_CD_REPO/docker:\/\/}:${LATEST_ARGO_TAG}"
REDIS_IMAGE_URL="${REDIS_REPO/docker:\/\/}:${LATEST_REDIS_TAG}"
ARGO_CD_IMAGE_TAG="${LATEST_ARGO_TAG}"

echo "Using Argo CD Image URL: ${ARGO_CD_IMAGE_URL}"
echo "Using Redis Image URL: ${REDIS_IMAGE_URL}"

cp microshift-gitops.spec.in microshift-gitops.spec

ARGO_CD_IMAGE_SHA_X86=$(skopeo inspect docker://${ARGO_CD_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="amd64") | .digest')
ARGO_CD_IMAGE_SHA_ARM=$(skopeo inspect docker://${ARGO_CD_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="arm64") | .digest')

REDIS_IMAGE_SHA_X86=$(skopeo inspect docker://${REDIS_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="amd64") | .digest')
REDIS_IMAGE_SHA_ARM=$(skopeo inspect docker://${REDIS_IMAGE_URL} --raw | jq -r '.manifests[] | select(.platform.architecture=="arm64") | .digest')

echo "Replacing placeholders in microshift-gitops.spec..."
sed -i "s|REPLACE_ARGO_CD_CONTAINER_SHA_X86|${ARGO_CD_IMAGE_SHA_X86}|g" microshift-gitops.spec
sed -i "s|REPLACE_ARGO_CD_CONTAINER_SHA_ARM|${ARGO_CD_IMAGE_SHA_ARM}|g" microshift-gitops.spec
sed -i "s|REPLACE_ARGO_CD_VERSION|${ARGO_CD_IMAGE_TAG}|g" microshift-gitops.spec

sed -i "s|REPLACE_REDIS_CONTAINER_SHA_X86|${REDIS_IMAGE_SHA_X86}|g" microshift-gitops.spec
sed -i "s|REPLACE_REDIS_CONTAINER_SHA_ARM|${REDIS_IMAGE_SHA_ARM}|g" microshift-gitops.spec

echo "Script finished successfully."