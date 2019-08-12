This is a prototype application for populating a WAE planfile with network collection from the WAE API.  
Data is parsed from JSON files created by the EPNM collector application.

**Setup**

1) Add a CLI template to EPNM for retrieving the MPLS database from IOS-XR node (must be XR for this to work).

`   Template name "show mpls traffic-eng topology".
    Device type should be XR device (e.g. NCS4000, NCS5500, ASR9000)
    Template command "do show mpls traffic-eng topology isis brief"`
    
Also add CLI template to get ISIS hostnames...
    
    Template name "show isis hostname"
    Device type should be XR device (e.g. NCS4000, NCS5500, ASR9000)
    Template command "do show isis hostname"
    
2) Create a virtual environment for Python 2.7

3) Activate the virtual environment

    Example Linux...
    [gibson@ibanez ~]$ source ./VirtualEnvs/wae_api_venv/bin/activate
    (wae_api_venv) [gibson@ibanez ~]$
    
    Example Windows...
    C:\Users\brfoster>virtualenvs\WAE_API_27_64\Scripts\activate
    (WAE_API_27_64) C:\Users\brfoster>

4) Install requests

    (wae_api_venv) [gibson@ibanez ~]$ pip install requests

5) Follow the directions for WAE Python environment setup from the WAE API documentation

    https://developer.cisco.com/docs/wan-automation-engine/#wae-design-rpc-api
    
    Example .bashrc entries...
    
    export CARIDEN_HOME=/usr/local/wae_install
    
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CARIDEN_HOME/lib
    
    export PYTHONPATH=$PYTHONPATH:$CARIDEN_HOME/lib/python

6) Run the collector

    Usage:
    
    `python wae_api.py <path to archive directory> <seed node host name and domain> <ip address of EPNM> <EPNM user> <EPNM password> <phases> <build_plan>`
    
    Example,
    
    (wae_api_venv) [gibson@ibanez ~]$ python wae_api.py "C:\Users\brfoster\Temp" "NCS4K-Site2.cisco.com" "10.135.7.222" "root" "Epnm1234" "135" 0
