#!/bin/sh

set -xe

echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup
echo 'DPkg::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };' > /etc/apt/apt.conf.d/docker-clean
echo 'APT::Update::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };' >> /etc/apt/apt.conf.d/docker-clean
echo 'Dir::Cache::pkgcache ""; Dir::Cache::srcpkgcache "";' >> /etc/apt/apt.conf.d/docker-clean
echo 'Acquire::Languages "none";' > /etc/apt/apt.conf.d/docker-no-languages
cat /etc/apt/apt.conf.d/docker-no-languages

