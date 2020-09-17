This is a prototype application for populating a WAE planfile with network collection from the WAE API.  
Data is parsed from JSON files created by the Blue Planet Ciena collector application.

**Setup**
    
1) Create a virtual environment for Python 2.7

2) Activate the virtual environment

    Example Linux...
    [gibson@ibanez ~]$ source ./VirtualEnvs/wae_api_venv/bin/activate
    (wae_api_venv) [gibson@ibanez ~]$
    
    Example Windows...
    C:\Users\brfoster>virtualenvs\WAE_API_27_64\Scripts\activate
    (WAE_API_27_64) C:\Users\brfoster>

3) Install requirements

    (wae_api_venv) [gibson@ibanez ~]$ pip install -r requirements.txt

5) Follow the directions for WAE Python environment setup from the WAE API documentation

    https://developer.cisco.com/docs/wan-automation-engine/#wae-design-rpc-api
    
    Example .bashrc entries...
    
    export CARIDEN_HOME=/usr/local/wae_install
    
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CARIDEN_HOME/lib
    
    export PYTHONPATH=$PYTHONPATH:$CARIDEN_HOME/lib/python

6) Run the collector

    Usage:
    
    `python wae_api.py <path to archive directory> <ip address of Ciena> <Ciena user> <Ciena password> <logging> <build_plan>`<delete-previous(optional)>
    
    Example,
    
    (wae_api_venv) [gibson@ibanez ~]$ python wae_api.py "C:\Users\brfoster\Temp" "10.135.7.222" "root" "Ciena1234" "info" -b -d

    NOTE: if no parameters will pass then all default parameters will pick from confiig file. build (-b) parameter is mandatory to build the plan file.
