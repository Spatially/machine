Parcels
=======

### Overview

This script will fetch the latest [state.txt](http://results.openaddresses.io/state.txt) file, and parse as much parcel data as it can.

### Installation

* Tested on Ubuntu 16.04 server. 8GB RAM.

```
# Install pre-requisites and prepare a Python virtual environment.
apt-get install libgdal-dev python3-pip libffi-dev python3-cairo python3-gdal
pip3 install virtualenv
python3 -m virtualenv --system-site-packages ./env && source ./env/bin/activate

# Install OpenAddresses parcels code.
git clone https://github.com/openaddresses/machine.git
cd machine && pip3 install -r requirements.txt

cd openaddr
export PYTHONPATH=${PWD}
cd parcels

# Download all parcel data sources.
git clone https://github.com/openaddresses/openaddresses.git openaddresses
(cd openaddresses; npm install)

python3 -u -m parcels.parse
```
