#debuginfo not supported with Go
%global debug_package %{nil}

%global package_name microshift-gitops
%global product_name OpenShift GitOps (ArgoCD) components for MicroShift
%global microshift_gitops_version 0.0.1
%global microshift_gitops_release %(echo ${CI_SPEC_RELEASE} | sed -e s/rhel-9-//g)
%global commitid 3.0.11
%global source_dir argo-cd-%{commitid}
%global source_tar argo-cd-%{commitid}.tar.gz

Name:           %{package_name}
Version:        %{microshift_gitops_version}
Release:        %{microshift_gitops_release}%{?dist}
Summary:        The %{product_name} package provides the required kustomize manifests for the OpenShift GitOps (ArgoCD) components to be installed on MicroShift.
License:        ASL 2.0
URL:            https://github.com/argoproj/argo-cd/archive/refs/tags/v%{commitid}.tar.gz

Source0:        %{source_tar}
BuildRequires:  sed
Provides:       %{package_name}
Obsoletes:      %{package_name}
Requires:       microshift >= 4.14

%description
%{summary}

%package release-info
Summary: Release information for MicroShift GitOps
BuildArch: noarch

%description release-info
The %{package_name}-release-info package provides release information files for this
release. These files contain the list of container image references used by
MicroShift GitOps and can be used to embed those images into osbuilder blueprints.
An example of such osbuilder blueprints for x86_64 and aarch64 platforms are
also included in the package.

%prep
%setup -q -n %{source_dir}

%build

# Remove runAsUser property set in redis deployment as it causes deployments in microshift to fail security constratint context (SCC)
sed -i '/^[[:space:]]\+runAsUser: 999$/d' "manifests/base/redis/argocd-redis-deployment.yaml"

# Remove server related Cluster RBAC policies
rm -rf "manifests/cluster-rbac/server"
sed -i '/- .\/server/d' "manifests/cluster-rbac/kustomization.yaml"
sed -i '/- .\/applicationset-controller/d' "manifests/cluster-rbac/kustomization.yaml"

# Change the namespace of the service account from argocd to openshift-gitops
sed -i 's/namespace: .*/namespace: openshift-gitops/g' "manifests/cluster-rbac/application-controller/argocd-application-controller-clusterrolebinding.yaml"

# Change the imagePullPolicy to IfNotPresent to support disconnected environment usecase
sed -i 's/imagePullPolicy: Always/imagePullPolicy: IfNotPresent/g' "manifests/base/application-controller/argocd-application-controller-statefulset.yaml"
sed -i 's/imagePullPolicy: Always/imagePullPolicy: IfNotPresent/g' "manifests/base/repo-server/argocd-repo-server-deployment.yaml"
sed -i 's/imagePullPolicy: Always/imagePullPolicy: IfNotPresent/g' "manifests/base/redis/argocd-redis-deployment.yaml"

# Manifest file for creating the openshift-gitops namespace
mkdir -p "manifests/microshift-gitops/"
cat <<EOF > "manifests/microshift-gitops/namespace.yaml"
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-gitops
EOF

# Add the required args for the redis container image available in Red Hat repositories. This is different from the redis7 image used by the upstream.
cat <<EOF >"manifests/microshift-gitops/redis-patch-args.yaml"
- op: add
  path: /spec/template/spec/containers/0/args/0
  value: "redis-server"
- op: add
  path: /spec/template/spec/containers/0/args/1
  value: "--protected-mode"
- op: add
  path: /spec/template/spec/containers/0/args/2
  value: "no"
EOF

# Create Kustomization files
cat <<EOF >"manifests/microshift-gitops/kustomization.yaml"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: openshift-gitops
resources:
  - namespace.yaml
  - application-controller
  - cluster-rbac
  - config
  - crds
  - redis
  - repo-server
patches:
  - path: redis-patch-args.yaml
    target:
      kind: Deployment
      name: argocd-redis
      labelSelector: app.kubernetes.io/part-of=argocd
EOF

#TODO: Find a better way to do away with the hardcoded image URLs
%ifarch arm64 aarch64
cat <<EOF >>"manifests/microshift-gitops/kustomization.yaml"
images:
  - name: quay.io/argoproj/argocd
    newName: registry.redhat.io/openshift-gitops-1/argocd-rhel9
    digest: "sha256:e9f89c838a37794fe47d6aa5496f9db2d604e38ed51193e236191dbff0e41c92"
  - name: redis
    newName: registry.redhat.io/rhel9/redis-6
    digest: "sha256:c19f537eaf582bfa164717ddcf76a51a1b50abdd798d4314f345df7bcc7cec10"
EOF
%endif

%ifarch x86_64
cat <<EOF >>"manifests/microshift-gitops/kustomization.yaml"
images:
  - name: quay.io/argoproj/argocd
    newName: registry.redhat.io/openshift-gitops-1/argocd-rhel9
    digest: "sha256:78c0715198d0d9dc8f4fc25197423412eabd5fd4d82151a41f3568a74c4e7317"
  - name: redis
    newName: registry.redhat.io/rhel9/redis-6
    digest: "sha256:e96c0a8cc1632130386dd77e4dc808f0661e79e8397d13c694f5e0eced63ede5"
EOF
%endif

#GitOps release-info artifacts
mkdir -p "microshift-assets"
cat <<EOF >"microshift-assets/release-gitops-arm64.json"
{
  "release": {
    "base": "1.16.1-1"
  },
  "images": {
    "openshift-gitops-argocd": "registry.redhat.io/openshift-gitops-1/argocd-rhel9@sha256:e9f89c838a37794fe47d6aa5496f9db2d604e38ed51193e236191dbff0e41c92",
    "redis": "registry.redhat.io/rhel9/redis-6@sha256:c19f537eaf582bfa164717ddcf76a51a1b50abdd798d4314f345df7bcc7cec10"
  }
}
EOF

cat <<EOF >"microshift-assets/release-gitops-x86_64.json"
{
  "release": {
    "base": "1.16.1-1"
  },
  "images": {
    "openshift-gitops-argocd": "registry.redhat.io/openshift-gitops-1/argocd-rhel9@sha256:78c0715198d0d9dc8f4fc25197423412eabd5fd4d82151a41f3568a74c4e7317",
    "redis": "registry.redhat.io/rhel9/redis-6@sha256:e96c0a8cc1632130386dd77e4dc808f0661e79e8397d13c694f5e0eced63ede5"
  }
}
EOF

cat <<'EOF' >"microshift-assets/microshift_running_check_gitops.sh"
#!/bin/bash

set -eu -o pipefail

SCRIPT_NAME=$(basename "$0")
CHECK_DEPLOY_NS="openshift-gitops"

# Source the MicroShift health check functions library
source /usr/share/microshift/functions/greenboot.sh

# Set the term handler to convert exit code to 1
trap 'forced_termination' TERM SIGINT

# Set the exit handler to log the exit status
trap 'log_script_exit' EXIT

# Handler that will be called when the script is terminated by sending TERM or
# INT signals. To override default exit codes it forces returning 1 like the
# rest of the error conditions throughout the health check.
function forced_termination() {
    echo "Signal received, terminating."
    exit 1
}

# Exit if the current user is not 'root'
if [ "$(id -u)" -ne 0 ] ; then
    echo "The '${SCRIPT_NAME}' script must be run with the 'root' user privileges"
    exit 1
fi

echo "STARTED"

# Print the boot variable status
print_boot_status

# Exit if the MicroShift service is not enabled
if [ "$(systemctl is-enabled microshift.service 2>/dev/null)" != "enabled" ] ; then
    echo "MicroShift service is not enabled. Exiting..."
    exit 0
fi

# Set the wait timeout for the current check based on the boot counter
WAIT_TIMEOUT_SECS=$(get_wait_timeout)

LOG_POD_EVENTS=true

# Wait for the deployments to be ready
echo "Waiting ${WAIT_TIMEOUT_SECS}s for '${CHECK_DEPLOY_NS}' deployments to be ready"
if ! wait_for "${WAIT_TIMEOUT_SECS}" namespace_deployment_ready ; then
    echo "Error: Timed out waiting for '${CHECK_DEPLOY_NS}' deployments to be ready"
    exit 1
fi
EOF

%install

# GitOps manifests
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/crds
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller-roles
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/config
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/redis
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/repo-server
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac
install -d -m755 %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac/application-controller
install -d -m755 %{buildroot}%{_sysconfdir}/greenboot/check/required.d

# Copy all the GitOps manifests except the arch specific ones
install -p -m644 manifests/microshift-gitops/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/
install -p -m644 manifests/crds/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/crds
install -p -m644 manifests/base/application-controller/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller
install -p -m644 manifests/base/application-controller-roles/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller-roles
install -p -m644 manifests/base/config/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/config
install -p -m644 manifests/base/redis/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/redis
install -p -m644 manifests/base/repo-server/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/repo-server
install -p -m644 manifests/cluster-rbac/kustomization.yaml %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac
install -p -m644  manifests/cluster-rbac/application-controller/* %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac/application-controller
install -p -m755 microshift-assets/microshift_running_check_gitops.sh %{buildroot}%{_sysconfdir}/greenboot/check/required.d/60_microshift_running_check_gitops.sh

mkdir -p -m755 %{buildroot}%{_datadir}/microshift/release
install -p -m644 microshift-assets/release-gitops* %{buildroot}%{_datadir}/microshift/release/

# TODO: Test to see if the kustomize directories are set correctly.
# kustomize build %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops
# oc create -k %{buildroot}/%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops --dry-run=client --validate=false

%files
%license LICENSE
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/crds
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller-roles
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/config
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/redis
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/repo-server
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac
%dir %{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac/application-controller
%dir %{_sysconfdir}/greenboot/check/required.d
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/crds/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/application-controller-roles/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/config/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/redis/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/repo-server/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac/*
%{_prefix}/lib/microshift/manifests.d/020-microshift-gitops/cluster-rbac/application-controller/*
%{_sysconfdir}/greenboot/check/required.d/60_microshift_running_check_gitops.sh

%files release-info
%dir %{_datadir}/microshift
%dir %{_datadir}/microshift/release

%{_datadir}/microshift/release/release-gitops*.json

%changelog
* Tue Jan 09 2024 Anand Francis Joseph <anjoseph@redhat.com>
- initial commit