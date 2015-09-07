#!/bin/sh
set -xe

echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup
cat <<EOF > /etc/apt/apt.conf.d/docker-clean
DPkg::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };
APT::Update::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };

Dir::Cache::pkgcache ""; Dir::Cache::srcpkgcache "";

Acquire::Languages "none";

APT::Install-Recommends=false;
APT::Install-Suggests=false;
EOF

apt update
apt install -qy apt-transport-https
apt-get clean

# Use NginX upstream versions
apt-key add - <<EOF
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (FreeBSD)

mQENBE5OMmIBCAD+FPYKGriGGf7NqwKfWC83cBV01gabgVWQmZbMcFzeW+hMsgxH
W6iimD0RsfZ9oEbfJCPG0CRSZ7ppq5pKamYs2+EJ8Q2ysOFHHwpGrA2C8zyNAs4I
QxnZZIbETgcSwFtDun0XiqPwPZgyuXVm9PAbLZRbfBzm8wR/3SWygqZBBLdQk5TE
fDR+Eny/M1RVR4xClECONF9UBB2ejFdI1LD45APbP2hsN/piFByU1t7yK2gpFyRt
97WzGHn9MV5/TL7AmRPM4pcr3JacmtCnxXeCZ8nLqedoSuHFuhwyDnlAbu8I16O5
XRrfzhrHRJFM1JnIiGmzZi6zBvH0ItfyX6ttABEBAAG0KW5naW54IHNpZ25pbmcg
a2V5IDxzaWduaW5nLWtleUBuZ2lueC5jb20+iQE+BBMBAgAoBQJOTjJiAhsDBQkJ
ZgGABgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRCr9b2Ce9m/YpvjB/98uV4t
94d0oEh5XlqEZzVMrcTgPQ3BZt05N5xVuYaglv7OQtdlErMXmRWaFZEqDaMHdniC
sF63jWMd29vC4xpzIfmsLK3ce9oYo4t9o4WWqBUdf0Ff1LMz1dfLG2HDtKPfYg3C
8NESud09zuP5NohaE8Qzj/4p6rWDiRpuZ++4fnL3Dt3N6jXILwr/TM/Ma7jvaXGP
DO3kzm4dNKp5b5bn2nT2QWLPnEKxvOg5Zoej8l9+KFsUnXoWoYCkMQ2QTpZQFNwF
xwJGoAz8K3PwVPUrIL6b1lsiNovDgcgP0eDgzvwLynWKBPkRRjtgmWLoeaS9FAZV
ccXJMmANXJFuCf26iQEcBBABAgAGBQJOTkelAAoJEKZP1bF62zmo79oH/1XDb29S
YtWp+MTJTPFEwlWRiyRuDXy3wBd/BpwBRIWfWzMs1gnCjNjk0EVBVGa2grvy9Jtx
JKMd6l/PWXVucSt+U/+GO8rBkw14SdhqxaS2l14v6gyMeUrSbY3XfToGfwHC4sa/
Thn8X4jFaQ2XN5dAIzJGU1s5JA0tjEzUwCnmrKmyMlXZaoQVrmORGjCuH0I0aAFk
RS0UtnB9HPpxhGVbs24xXZQnZDNbUQeulFxS4uP3OLDBAeCHl+v4t/uotIad8v6J
SO93vc1evIje6lguE81HHmJn9noxPItvOvSMb2yPsE8mH4cJHRTFNSEhPW6ghmlf
Wa9ZwiVX5igxcvaIRgQQEQIABgUCTk5b0gAKCRDs8OkLLBcgg1G+AKCnacLb/+W6
cflirUIExgZdUJqoogCeNPVwXiHEIVqithAM1pdY/gcaQZmIRgQQEQIABgUCTk5f
YQAKCRCpN2E5pSTFPnNWAJ9gUozyiS+9jf2rJvqmJSeWuCgVRwCcCUFhXRCpQO2Y
Va3l3WuB+rgKjsQ=
=A015
-----END PGP PUBLIC KEY BLOCK-----
EOF
echo "deb http://nginx.org/packages/debian/ jessie nginx" >> /etc/apt/sources.list.d/nginx.list

# Use our private debian repo
apt-key add - <<EOF
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2

mQENBFXpXDgBCACo4Vatrhne4IrRO9/MqHNmvctb7wJJGdRu3fM+Ij909LO3bpF1
cr/8GQhjiYAKNTwNIymDiwfqZRq0sQHj/tv+z8SkS/QlaRycA67HKCzb7Add4aTI
YeNkna1TYnkBnPtVhCdlnfGCxKIldzydsUC1sVOu0rNg2TzHgVjtRpuzaxBddaKB
vTG5FPb3a/v1ewuoT8cODl2wsYApsL2wZ7WSJbOg0LwQcSEq4jKpt8/HjkQwGlVF
uh+nSWTRzNB7t6wQ0DclANzx1YZzI/T+BdFvw9BtWCflxrrozqN/ENmyIZZW3dg3
dm/m1GoyDS/gS+GZ1MPfsBktPnLUjE4zojANABEBAAG0LFBvbHljb25zZWlsIERl
diBUZWFtIDxkZXZvcHNAcG9seWNvbnNlaWwuZnI+iQE3BBMBCgAhBQJV6Vw4Ahsv
BQsJCAcDBRUKCQgLBRYCAwEAAh4BAheAAAoJEEN79TgHYRMjbfMH/iqznoaVJDYU
RSKOn7ln8kJt4ivMsUH6YzYbC8uCzt+ChJs0pstgR5KOTsf6k0j3xEYPuKN9yeCY
hXEo+468wVxH0tkkX98cxBicJM+b/APnE/HyWV6V8xsIo06ozOgGBYdBZ39WY0Lg
ggBkdDgmn7UTJisGQqcki6qLCwqVXOnk+auGfm7tlD1st2ZwKtFbUW54IQgEyru5
7fkR4zxuCcfdUy6ThTo/XYyMyz/WS18zWHLFb+1iC23gcG4Pau4Z0TegK1hVJclb
L1+yECVhPSlfVwac5jIyfzrfOL9JNuoH3MVk2qq6Sexzg8xaoEGYur4FXYocWIgT
mxU9jhbqn08=
=pw6K
-----END PGP PUBLIC KEY BLOCK-----
EOF
echo "deb https://debian.polydev.blue/ grocker main" >> /etc/apt/sources.list.d/polydev.list
