#!/bin/sh
rm -rf build
mkdir build
cd build
cmake -DBUILD_IPOE_DRIVER=TRUE -DBUILD_VLAN_MON_DRIVER=TRUE -DCMAKE_INSTALL_PREFIX=/usr -DKDIR=/usr/src/linux-headers-`uname -r` -DLUA=TRUE -DNETSNMP=TRUE -DCPACK_TYPE=Ubuntu22 ..
make -j 16
cpack -G DEB
sudo dpkg -i accel-ppp-1.12.0-Linux.deb
