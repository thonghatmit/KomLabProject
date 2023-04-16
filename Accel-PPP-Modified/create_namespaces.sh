#!/bin/sh
sudo ip netns add NamespaceA
sudo ip netns add NamespaceB
echo "Namespaces:"
ip netns list
sudo ip link add dev veth-A-Client type veth peer name veth-A
sudo ip link add dev veth-B-Client type veth peer name veth-B
sudo ip link set veth-A netns NamespaceA
sudo ip link set veth-B netns NamespaceB

sudo ip -n NamespaceA addr add 192.168.42.1/24 dev veth-A
sudo ip -n NamespaceB addr add 192.168.43.1/24 dev veth-B
sudo ip addr add 192.42.0.1/24 dev veth-A-Client
sudo ip addr add 192.43.0.1/24 dev veth-B-Client

sudo ip link set veth-A-Client up
sudo ip link set veth-B-Client up
sudo ip -n NamespaceA link set veth-A up
sudo ip -n NamespaceB link set veth-B up

sudo ip -n NamespaceA link set up dev lo
sudo ip -n NamespaceB link set up dev lo

sudo ip -n NamespaceA route add 192.42.0.0/24 dev veth-A
sudo ip route add 192.168.42.0/24 dev veth-A-Client
sudo ip -n NamespaceB route add 192.43.0.0/24 dev veth-B
sudo ip route add 192.168.43.0/24 dev veth-B-Client


echo "Network interfaces on host:"
ip link
echo "Network interfaces in Namespace A:"
sudo ip netns exec NamespaceA ip link
echo "Network interfaces in Namespace B:"
sudo ip netns exec NamespaceB ip link
