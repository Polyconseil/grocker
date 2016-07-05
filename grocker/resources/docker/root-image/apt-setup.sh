#!/bin/sh
set -xe

# Adapt APT config for Docker
echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup
cat <<EOF > /etc/apt/apt.conf.d/docker-clean
DPkg::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };
APT::Update::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };

Dir::Cache::pkgcache ""; Dir::Cache::srcpkgcache "";

Acquire::Languages "none";

APT::Install-Recommends=false;
APT::Install-Suggests=false;
EOF
