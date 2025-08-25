#debuginfo not supported with Go
%global _enable_debug_package 0
%global debug_package %{nil}
%global __os_install_post /usr/lib/rpm/brp-compress %{nil}

%global package_name openshift-gitops-argocd-cli
%global product_name OpenShift GitOps ArgoCD CLI
%global golang_version 1.22
%global argocd_cli_version ${CI_X_VERSION}.${CI_Y_VERSION}.${CI_Z_VERSION}
%global argocd_cli_release %(echo ${CI_SPEC_RELEASE} | sed -e s/rhel-9-//g)
%global commitid ${CI_ARGO_CD_UPSTREAM_COMMIT}
%global source_dir argo-cd-%{commitid}
%global source_tar argo-cd-${CI_ARGO_CD_UPSTREAM_COMMIT}.tar.gz
%global vendor_modules_file vendor/modules.txt



Name:           %{package_name}
Version:        %{argocd_cli_version}
Release:        %{argocd_cli_release}%{?dist}
Summary:        %{product_name} OpenShift GitOps ArgoCD CLI tool
License:        ASL 2.0
URL:            https://github.com/argoproj/argo-cd/commit/%{commitid}

Source0:        %{source_tar}
BuildRequires:  golang >= %{golang_version}
Provides:       %{package_name}
Obsoletes:      %{package_name}

%description
%{summary}

%package redistributable
Summary:        %{product_name} ArgoCD CLI binaries for Linux, Mac OSX, and Windows
BuildRequires:  golang >= %{golang_version}
Provides:       %{package_name}-redistributable
Obsoletes:      %{package_name}-redistributable

%description redistributable
%{summary}

%prep
%setup -q -n %{source_dir}
mkdir -p %{_builddir}/src
%global make CURRENT_DIR=%{_builddir} LDFLAGS='' GIT_COMMIT=%{commitid} GIT_TREE_STATE=clean EXTRA_BUILD_INFO="openshift-gitops-version: %{argocd_cli_version}, release: %{argocd_cli_release}" make

%build
if [ -f "%{vendor_modules_file}" ]; then
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-darwin-amd64 GOOS=darwin GOARCH=amd64 argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-darwin-arm64 GOOS=darwin GOARCH=arm64 argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-linux-amd64 GOOS=linux GOARCH=amd64 argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-linux-arm64 GOOS=linux GOARCH=arm64 argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-linux-ppc64le GOOS=linux GOARCH=ppc64le argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-linux-s390x GOOS=linux GOARCH=s390x argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-windows-amd64.exe GOOS=windows GOARCH=amd64 argocd-all
  %{make} GIT_TAG="v$(cat VERSION)" GOFLAGS="-mod=vendor" BIN_NAME=argocd-windows-arm64.exe GOOS=windows GOARCH=arm64 argocd-all
fi


%install
install -d %{buildroot}%{_datadir}/%{name}/
echo "%{_datadir}/%{name}/" > filelist.txt
if [ -f "%{vendor_modules_file}" ]; then
  install -d %{buildroot}%{_bindir}
  install -p -m 0755 dist/argocd-linux-$(go env GOHOSTARCH) %{buildroot}%{_bindir}/argocd
  echo "%{_bindir}/argocd" > filelist.txt
fi

%ifarch x86_64
install -d %{buildroot}%{_datadir}/%{name}-redistributable/{linux,macos,windows}
echo "%{_datadir}/%{name}-redistributable/linux/"> redistributable_filelist.txt
echo "%{_datadir}/%{name}-redistributable/macos/">> redistributable_filelist.txt
echo "%{_datadir}/%{name}-redistributable/windows/">> redistributable_filelist.txt
if [ -f "%{vendor_modules_file}" ]; then
  export DONT_STRIP=1
  install -p -m 0755 dist/argocd-linux-amd64 %{buildroot}%{_datadir}/%{name}-redistributable/linux/argocd-linux-amd64
  install -p -m 0755 dist/argocd-linux-arm64 %{buildroot}%{_datadir}/%{name}-redistributable/linux/argocd-linux-arm64
  install -p -m 0755 dist/argocd-linux-ppc64le %{buildroot}%{_datadir}/%{name}-redistributable/linux/argocd-linux-ppc64le
  install -p -m 0755 dist/argocd-linux-s390x %{buildroot}%{_datadir}/%{name}-redistributable/linux/argocd-linux-s390x
  install -p -m 0755 dist/argocd-darwin-amd64 %{buildroot}%{_datadir}/%{name}-redistributable/macos/argocd-darwin-amd64
  install -p -m 0755 dist/argocd-darwin-arm64 %{buildroot}%{_datadir}/%{name}-redistributable/macos/argocd-darwin-arm64
  install -p -m 0755 dist/argocd-windows-amd64.exe %{buildroot}%{_datadir}/%{name}-redistributable/windows/argocd-windows-amd64.exe
  install -p -m 0755 dist/argocd-windows-arm64.exe %{buildroot}%{_datadir}/%{name}-redistributable/windows/argocd-windows-arm64.exe
  echo "%{_datadir}/%{name}-redistributable/linux/argocd-linux-amd64" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/linux/argocd-linux-arm64" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/linux/argocd-linux-ppc64le" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/linux/argocd-linux-s390x" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/macos/argocd-darwin-amd64" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/macos/argocd-darwin-arm64" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/windows/argocd-windows-amd64.exe" >> redistributable_filelist.txt
  echo "%{_datadir}/%{name}-redistributable/windows/argocd-windows-arm64.exe" >> redistributable_filelist.txt
fi
%endif

%files -f filelist.txt
%license LICENSE

%ifarch x86_64
%files redistributable -f redistributable_filelist.txt
%license LICENSE
%endif

%changelog
* Thu Oct 26 2023 Anand Francis Joseph <anjoseph@redhat.com>
- initial commit
