import com.cisco.wae.design
#import json
import logging

from com.cisco.wae.design.model.net import HopType
#from com.cisco.wae.design.model.net import Network
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1LinkKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
#from com.cisco.wae.design.model.net.layer1 import L1CircuitPathKey
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
#from com.cisco.wae.design.model.net import SRLGRecord


def generateL1nodes(plan, l1nodelist):
    l1NodeManager = plan.getNetwork().getL1Network().getL1NodeManager()
    for l1node in l1nodelist:
        vendor = 'Ciena'
        model = 'Ciena6500'
        name = l1node['attributes']['name']
        # logging.debug('This is the node:\n{}'.format(l1node))
        longi = float(l1node['longitude'])
        lat = float(l1node['latitude'])
        site = l1node['siteName']
        l1nodeRec = L1NodeRecord(name=name, site=SiteKey(site), vendor=vendor, model=model, longitude=longi, latitude=lat)
        newl1node = l1NodeManager.newL1Node(l1nodeRec)

def generateL1links(plan, l1linksdict):
    l1LinkManager = plan.getNetwork().getL1Network().getL1LinkManager()
    for l1link in l1linksdict:
        # print(l1link['name'])
        l1nodeAKey = L1NodeKey(l1link['l1nodeA'])
        l1nodeBKey = L1NodeKey(l1link['l1nodeB'])
        description = l1link['description']
        # l1linkRec = L1LinkRecord(name=l1link['linkid'], l1NodeAKey=l1nodeAKey, l1NodeBKey=l1nodeBKey, description=description)
        l1linkRec = L1LinkRecord(name=l1link['linkname'], l1NodeAKey=l1nodeAKey, l1NodeBKey=l1nodeBKey, description=description)
        try:
            l1LinkManager.newL1Link(l1linkRec)
        except Exception as err:
            logging.warn("Could not add L1 link to the plan!")
            logging.warn(err)

def generateL1circuits(plan, l1_data):
        for l1data in l1_data:
            name = l1data['circuitName']
            if len(l1data.get('termination-points')) > 0:
                firstnode = l1data['termination-points'][0]['node']
                lastnode = l1data['termination-points'][1]['node']
                # l1hops, firstnode, lastnode = getfirstlastl1node(l1data['ordered_Hops'], firstl1node,
                #                                                          lastl1node)
                if 'Ordered L1 Hops' in  l1data:
                    firstl1node, lastl1node = getfirstlastl1node(l1data['Ordered L1 Hops'], firstnode,
                                                                            lastnode)
                    # if l1data['BW'] != '':
                    #     bw = int(l1data['BW'])
                    # else:
                    #     bw = 0
                    l1hops = l1data['Ordered L1 Hops']
                    portAname = l1data['portStartNode']
                    portBname = l1data['portEndNode']
                    status = l1data['status']
                    try:
                        generateL1circuit(plan, name, firstl1node, lastl1node, portAname, portBname, l1hops, 100000, status)
                        # generateL1circuit(plan, name, firstl1node, lastl1node, portAname, portBname, l1data['ordered_L1_Hops'], 100000, status)
                    except Exception as err:
                        logging.debug('could not add new port :{}'.format(err))

def getfirstlastl1node(orderedl1hops, firstnode, lastnode):
    l1hops = []
    firstl1node = ""
    lastl1node = ""

    for l1hop in orderedl1hops:
        firstlasthop = False
        if l1hop['nodeA'].split('-')[0] == firstnode.split('-')[0]: 
            firstlasthop = True
            firstl1node = l1hop['nodeA']
        elif l1hop['nodeB'].split('-')[0] == firstnode.split('-')[0]:
            firstlasthop = True
            firstl1node = l1hop['nodeB']
        elif l1hop['nodeA'].split('-')[0] == lastnode.split('-')[0]: 
            firstlasthop = True
            lastl1node = l1hop['nodeA']
        elif l1hop['nodeB'].split('-')[0] == lastnode.split('-')[0]:
            firstlasthop = True
            lastl1node = l1hop['nodeB']
    return firstl1node, lastl1node

def generateL1circuit(plan, name, l1nodeA, l1nodeB, l1portAname, l1portBname, l1hops, bw, status):
    l1portManager = plan.getNetwork().getL1Network().getL1PortManager()
    l1nodeAKey = L1NodeKey(l1nodeA)
    l1nodeBKey = L1NodeKey(l1nodeB)
    l1portRecA = L1PortRecord(name=l1portAname, l1Node=l1nodeAKey)
    l1portRecB = L1PortRecord(name=l1portBname, l1Node=l1nodeBKey)

    l1portManager.newL1Port(l1portRecA)
    l1portManager.newL1Port(l1portRecB)

    l1portAkey = L1PortKey(name=l1portAname, l1Node=l1nodeAKey)
    l1portBkey = L1PortKey(name=l1portBname, l1Node=l1nodeBKey)

    l1circuitrec = L1CircuitRecord(name=name, l1PortAKey=l1portAkey, l1PortBKey=l1portBkey, bandwidth=bw)

    l1circuitManager = plan.getNetwork().getL1Network().getL1CircuitManager()
    l1circuit = l1circuitManager.newL1Circuit(l1circuitrec)

    l1circKey = L1CircuitKey(l1PortAKey=l1portAkey, l1PortBKey=l1portBkey)
    l1circuitpathRec = L1CircuitPathRecord(l1CircKey=l1circKey, pathOption=1)
    l1circuitpathManager = plan.getNetwork().getL1Network().getL1CircuitPathManager()
    l1circuitpath = l1circuitpathManager.newL1CircuitPath(l1circuitpathRec)

    l1linkManager = plan.getNetwork().getL1Network().getL1LinkManager()

    hoptype = HopType('PathStrict', 1)
    l1hoprec = L1CircuitPathHopRecord(l1CircPathKey=l1circuitpath.getKey(), hopNode=L1NodeKey(l1nodeA), step=0,type=hoptype)
    l1circuitpath.addHop(l1hoprec)
    c = 1
    for l1hop in l1hops:
        l1_nodeA_key = L1NodeKey(l1hop['nodeA'])
        l1_nodeB_key = L1NodeKey(l1hop['nodeB'])
        l1_link_name = l1hop['linkname']
        l1_link_key = L1LinkKey(l1_link_name, l1_nodeA_key, l1_nodeB_key)
        # logging.debug('l1_link_key is :{}'.format(l1_link_name))
        l1_link = l1linkManager.getL1Link(l1_link_key)
        logging.debug('l1_link is :{}'.format(l1_link))
        try:
            l1hoprec = L1CircuitPathHopRecord(l1CircPathKey=l1circuitpath.getKey(), hopNode=l1_nodeA_key, hopLink=l1_link.getKey(), step=c, type=hoptype)
            l1circuitpath.addHop(l1hoprec)
            hops = l1circuitpath.getHops()
        except:
            logging.debug('could not add hop :{}'.format(err))

        c += 1
    return l1circuit