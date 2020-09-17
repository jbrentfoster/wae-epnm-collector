import com.cisco.wae.design
import logging

from com.cisco.wae.design.model.net import HopType
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1LinkKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
from com.cisco.wae.design.model.net import DemandKey
from com.cisco.wae.design.model.net import DemandEndpointKey
from com.cisco.wae.design.model.net import ServiceClassKey
from com.cisco.wae.design.model.net import LSPKey
from com.cisco.wae.design.model.traffic import DemandTrafficKey
from com.cisco.wae.design.model.net import TrafficLevelKey
# records
from com.cisco.wae.design.model.net import NodeRecord
from com.cisco.wae.design.model.net import SiteRecord
from com.cisco.wae.design.model.net import SiteKey
from com.cisco.wae.design.model.net.layer1 import L1NodeRecord
from com.cisco.wae.design.model.net.layer1 import L1LinkRecord
from com.cisco.wae.design.model.net.layer1 import L1PortRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathHopRecord
from com.cisco.wae.design.model.net import InterfaceRecord
from com.cisco.wae.design.model.net import CircuitRecord
from com.cisco.wae.design.model.net import DemandRecord
from com.cisco.wae.design.model.net import ServiceClassRecord
from com.cisco.wae.design.model.net import LSPRecord


def generateSites(plan, sitelist):
    SiteManager = plan.getNetwork().getSiteManager()
    for site in sitelist:
        logging.debug('This is the site:\n{}'.format(site))
        if check_site_exists(SiteManager, site['name']):
            # logging.warn(
            #     "site already exists in plan file, will not add duplicate: " + site['name'])
            continue
        long = float(site['longitude'])
        lat = float(site['latitude'])
        siteRec = SiteRecord(name=site['name'], longitude=long, latitude=lat, tags=[
                             site['id'], site['description']])
        newsite = SiteManager.newSite(siteRec)


def check_site_exists(SiteManager, site_name):
    all_sites = SiteManager.getAllSiteKeys()
    for site in all_sites:
        if site.name == site_name:
            # logging.info("site already exists in plan, skipping this one...")
            return True
    return False
