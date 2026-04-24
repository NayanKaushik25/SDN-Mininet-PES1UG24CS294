# SDN Mininet Project - Traffic Monitoring and Statistics Collector

## Overview
This project demonstrates Software Defined Networking (SDN) using Mininet and a custom POX controller. It captures network traffic in real time, logs packet statistics to a CSV file, and visualizes traffic using Python.

## Features
- Custom Mininet topology
- POX controller for monitoring traffic
- Real-time packet counting
- CSV logging of traffic data
- Visualization using Matplotlib

## Tech Stack
- Python
- Mininet
- POX Controller
- Pandas
- Matplotlib
- Linux (Ubuntu recommended)

## Project Structure
SDN-Mininet-PES1UG24CS294/
- pox/traffic_monitor.py
- mininet/topology.py
- traffic_report.csv
- plot.py
- README.md

## Installation and Setup

Run the following commands in order:

```bash
# Install Mininet
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a

# Install POX
cd ..
git clone https://github.com/noxrepo/pox

# Install Python dependencies
pip install pandas matplotlib


# Start POX controller
cd pox
./pox.py log.level --DEBUG traffic_monitor

# In a new terminal, run Mininet topology (example)
sudo mn -c
sudo mn --topo single,2 --controller remote,ip=127.0.0.1,port=6633 --switch ovsk 

# Inside Mininet CLI
pingall
iperf

# After exiting Mininet, visualize results
python3 plot.py
