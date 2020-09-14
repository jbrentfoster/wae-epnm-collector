import com.cisco.wae.design
#import json
import logging

from com.cisco.wae.design.model.net import HopType
#from com.cisco.wae.design.model.net import Network
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
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
from com.cisco.wae.design.model.net import InterfaceRecord
from com.cisco.wae.design.model.net import CircuitRecord
from com.cisco.wae.design.model.net import DemandRecord
from com.cisco.wae.design.model.net import ServiceClassRecord
from com.cisco.wae.design.model.net import LSPRecord
#Imported the l3 modules. Testing to see if this configuration is valid.
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1LinkKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathKey
from com.cisco.wae.design.model.net.layer1 import L1NodeRecord
from com.cisco.wae.design.model.net.layer1 import L1LinkRecord
from com.cisco.wae.design.model.net.layer1 import L1PortRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathHopRecord
#from com.cisco.wae.design.model.net import SRLGRecord


def generateL3nodes(plan, l3nodelist):
    l3NodeManager = plan.getNetwork().getl3Network().getl3NodeManager()
    for l3node in l3nodelist:
        vendor = 'Ciena'
        model = 'Ciena6500'
        name = l3node['attributes']['name']
        logging.debug('This is the node:\n{}'.format(l3node))
        long = float(l3node['longitude'])
        lat = float(l3node['latitude'])
        site = l3node['wae_site_name']
        l3nodeRec = NodeRecord(name=name, site=SiteKey(site), vendor=vendor, model=model, longitude=long, latitude=lat)
        newl3node = l3NodeManager.newl3Node(l3nodeRec)

#Use this version if the previous version doesn't work due to the l3nodemanager library
# def generateL3nodes(plan, l3nodelist):
#     for l3node in l3nodelist:
#         vendor = 'Ciena'
#         model = 'Ciena6500'
#         name = l3node['attributes']['name']
#         logging.debug('This is the node:\n{}'.format(l3node))
#         long = float(l3node['longitude'])
#         lat = float(l3node['latitude'])
#         site = l3node['wae_site_name']
#         l3nodeRec = NodeRecord(name=name, site=SiteKey(site), vendor=vendor, model=model, longitude=long, latitude=lat)
#         newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec)


################################
################################

#The L3 circuit portion of the plan file is compeltely untested. I have stubbed in the code from the 'wae_api.py' script, modify as necessary for the Ciena script

################################
################################

# def generateL3circuits(plan, l3linksdict):
#     i = 0
#     linkslist = []
#     duplicatelink = False
#     circ_srlgs = {}
#     circuit_name_list = []
#     #Seek from Brent and Andrew here. Kathy provided a list of network elements that i pared down and formatted, then used it in this script as a crossreference. She may need to provide a similar list for Ciena, the 'may_19_circuit_names.csv' file is in the wae_api branch.
#     name_reader = csv.DictReader(open('configs/may_19_circuit_names.csv'), fieldnames=('0', '1', '2', '3', '4', '5'))
#     for row in name_reader:
#         circuit_name_list.append(row)

#     for k1, v1 in l3linksdict.items():
#         # logging.info "**************Nodename is: " + k1
#         firstnode = k1
#         # if firstnode == "LYBRNYLB-01153A08A":
#         #     pass
#         for k2, v2 in v1.items():
#             if isinstance(v2, dict):
#                 for k3, v3 in v2.items():
#                     # logging.warn "***************Linkname is: " + k3
#                     lastnode = v3['Neighbor']
#                     if lastnode == "NYCKNYAL-0223502A":
#                         pass
#                     discoveredname = v3['discoveredname']
#                     affinity = v3['Affinity']
#                     firstnode_ip = [v3['Local IP']]
#                     firstnode_intf = v3['Local Intf']
#                     lastnode_ip = [v3['Neighbor IP']]
#                     lastnode_intf = v3['Neighbor Intf']
#                     te_metric = int(v3['TE Metric'])
#                     igp_metric = int(v3['IGP Metric'])
#                     phy_bw = float(v3['Phy BW'].split(' ')[0])
#                     rsvpbw = float(v3['RSVP BW'].split(' ')[0])
#                     intfbw = getintfbw(phy_bw)
#                     try:
#                         tp_description = v3['tp-description']
#                     except Exception as err:
#                         tp_description = ""

#                     srlgs = []
#                     if 'SRLGs' in v3:
#                         srlgs = v3['SRLGs']
#                     for linkdiscoveredname in linkslist:
#                         if discoveredname == linkdiscoveredname: duplicatelink = True
#                     if not duplicatelink:
#                         linkslist.append(discoveredname)
#                         name = ""
#                         if tp_description == "":
#                             for elem in circuit_name_list:
#                                 node_check = elem['1'] == firstnode and elem['3'] == lastnode
#                                 interface_check = elem['2'] == firstnode_intf and elem['4'] == lastnode_intf
#                                 if node_check and interface_check:
#                                     name = elem['0']
#                                     break
#                                 elif elem['1'] == firstnode and elem['2'].startswith('BDI'):
#                                     name = elem['0']
#                                     break
#                             if name == "":
#                                 i += 1
#                                 name = 'l3_circuit_{}/{}/{}'.format(int(i), firstnode, lastnode)
#                         else:
#                             if 'CktId: ' in tp_description:
#                                 name = tp_description.split('CktId: ')[1]
#                             # Fix - GLH - 2-18-19 #
#                             elif 'CID:' in tp_description:
#                                 name = tp_description.split('CID:')[1]
#                             # Fix End - GLH - 2-18-19 #
#                             else:
#                                 name = tp_description
#                         l3circuit = generateL3circuit(plan, name, firstnode, lastnode, affinity, firstnode_ip,
#                                                       lastnode_ip, firstnode_intf, lastnode_intf, igp_metric, te_metric)

#                         if l3circuit:
#                             if 'vc-fdn' in v3:
#                                 l1CircuitManager = plan.getNetwork().getL1Network().getL1CircuitManager()
#                                 l1circuits = l1CircuitManager.getAllL1Circuits()
#                                 for attr, val in l1circuits.items():
#                                     l1circuit_name = val.getName()
#                                     # logging.info("L1 circuit name is " + l1circuit_name)
#                                     if v3['vc-fdn'] == val.getName():
#                                         # logging.info("Name matched!")
#                                         l1circuit = l1CircuitManager.getL1Circuit(val.getKey())
#                                         l3circuit.setL1Circuit(l1circuit)
#                                         # TODO recode setting the L3 node site based on connected L1 node site
#                             l3circuit.setCapacity(intfbw)
#                             intfdict = l3circuit.getAllInterfaces()
#                             for k6, v6 in intfdict.items():
#                                 v6.setResvBW(int(rsvpbw / 1000))
#                             circ_name = l3circuit.getName()
#                             circ_key = l3circuit.getKey()
#                             circ_dict = {'SRLGs': srlgs, 'Circuit Key': circ_key, 'discoveredname': discoveredname}
#                             circ_srlgs[circ_name] = circ_dict
#                     duplicatelink = False

#     logging.info("Processing SRLG's...")
#     process_srlgs(plan, circ_srlgs)

def generateL3circuit(plan, name, l3nodeA, l3nodeB, affinity, l3nodeA_ip, l3nodeB_ip, nodeAintfname, nodeBintfname,
                      igp_metric, te_metric):
    nodeAKey = NodeKey(l3nodeA)
    nodeBKey = NodeKey(l3nodeB)
    # nodeAintfname = "L3_intf_" + name + "_to_" + l3nodeB
    # nodeBintfname = "L3_intf_" + name + "_to_" + l3nodeA

    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    # logging.warn bin(int(affinity, scale))[2:].zfill(num_of_bits)
    affinitylist = list(bin(int(affinity, scale))[2:].zfill(num_of_bits))

    affinities = []
    c = 0
    for afbit in reversed(affinitylist):
        if afbit == '1':
            affinities.append(c)
        c += 1
    intfArec = InterfaceRecord(sourceKey=nodeAKey, name=nodeAintfname, isisLevel=2, affinityGroup=affinities,
                               ipAddresses=l3nodeA_ip, igpMetric=igp_metric, teMetric=te_metric)
    intfBrec = InterfaceRecord(sourceKey=nodeBKey, name=nodeBintfname, isisLevel=2, affinityGroup=affinities,
                               ipAddresses=l3nodeB_ip, igpMetric=igp_metric, teMetric=te_metric)
    circRec = CircuitRecord(name=name)
    network = plan.getNetwork()
    try:
        circuit = network.newConnection(ifaceARec=intfArec, ifaceBRec=intfBrec, circuitRec=circRec)
        return circuit
    except Exception as err:
        logging.warn('Could not create circuit for: ' + name)
        logging.warn(err)