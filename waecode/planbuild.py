import com.cisco.wae.design
import flexlsp_creator
from com.cisco.wae.design.model.net import HopType
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathKey
from com.cisco.wae.design.model.net import DemandKey
from com.cisco.wae.design.model.net import DemandEndpointKey
from com.cisco.wae.design.model.net import ServiceClassKey
from com.cisco.wae.design.model.net import LSPKey
from com.cisco.wae.design.model.traffic import DemandTrafficKey
from com.cisco.wae.design.model.net import TrafficLevelKey
# records
from com.cisco.wae.design.model.net import NodeRecord
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


def generateL1nodes(plan, l1nodelist):
    l1NodeManager = plan.getNetwork().getL1Network().getL1NodeManager()
    for l1node in l1nodelist:
        l1nodeRec = L1NodeRecord(name=l1node['Name'])
        newl1node = l1NodeManager.newL1Node(l1nodeRec)
        newl1node.setLatitude(int(l1node['Y']))
        newl1node.setLongitude(int(l1node['X']))


def generateL1links(plan, l1linklist):
    l1LinkManager = plan.getNetwork().getL1Network().getL1LinkManager()
    for l1link in l1linklist:
        l1nodeAKey = L1NodeKey(l1link[0])
        l1nodeBKey = L1NodeKey(l1link[1])
        l1linkname = l1link[0] + "_" + l1link[1]
        l1linkRec = L1LinkRecord(name=l1linkname, l1NodeAKey=l1nodeAKey, l1NodeBKey=l1nodeBKey)
        l1LinkManager.newL1Link(l1linkRec)


def generateL1circuit(plan, name, l1nodeA, l1nodeB, l1hops, bw):
    l1portManager = plan.getNetwork().getL1Network().getL1PortManager()
    # l1portrecs = l1portManager.getAllL1PortRecords()
    l1nodeAKey = L1NodeKey(l1nodeA)
    l1nodeBKey = L1NodeKey(l1nodeB)
    l1portAname = name + '_port_to_' + l1nodeB
    l1portBname = name + '_port_to_' + l1nodeA
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

    orderedl1hops = []
    orderedl1hops.append(l1nodeA)
    for l1hop in l1hops:
        for node in l1hop:
            if node == l1nodeA:
                pass
            elif not node in orderedl1hops:
                orderedl1hops.append(node)
    c = 0
    for l1hop in orderedl1hops:
        if l1hop == l1nodeA:
            hoptype = HopType('PathStrict', 0)
        else:
            hoptype = HopType('PathLoose', 0)
        l1hoprec = L1CircuitPathHopRecord(l1CircPathKey=l1circuitpath.getKey(), hopNode=L1NodeKey(l1hop), step=c,
                                          type=hoptype)
        l1circuitpath.addHop(l1hoprec)
        c += 1

    return l1circuit


def generateL3nodes(plan, l3nodelist):
    for l3node in l3nodelist:
        nodeRec = NodeRecord(name=l3node['Name'])
        newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec)
        newl3node.setLatitude(int(l3node['Y']))
        newl3node.setLongitude(int(l3node['X']))


def generateL3circuit(plan, name, l3nodeA, l3nodeB):
    nodeAKey = NodeKey(l3nodeA)
    nodeBKey = NodeKey(l3nodeB)
    nodeAintfname = "L3_intf_" + name + "_to_" + l3nodeB
    nodeBintfname = "L3_intf_" + name + "_to_" + l3nodeA
    intfArec = InterfaceRecord(sourceKey=nodeAKey, name=nodeAintfname, isisLevel=2)
    intfBrec = InterfaceRecord(sourceKey=nodeBKey, name=nodeBintfname, isisLevel=2)
    circRec = CircuitRecord(name=name)
    network = plan.getNetwork()
    circuit = network.newConnection(ifaceARec=intfArec, ifaceBRec=intfBrec, circuitRec=circRec)

    return circuit


def generate_lsps(plan, lsps, l3nodeloopbacks, options, conn):
    index = 0
    for lsp in lsps:
        lspBW = int(int(lsp['signalled-bw']) / 1000)
        direction = lsp['direction']
        index += 1
        if lspBW > 0:
            tuID = lsp['Tunnel ID']
            lspName = lsp['fdn'].split('!')[1].split('=')[1]
            demandName = "Demand for " + lspName
            src = getnodename(lsp['Tunnel Source'], l3nodeloopbacks)
            dest = getnodename(lsp['Tunnel Destination'], l3nodeloopbacks)
            if direction == "ns4:bi-direction":
                nodes = [src, dest]
                flexlsp_creator.createflexlsp(options,conn,plan,nodes,lspName,lspBW)
                new_demand_for_LSP(plan, src, dest, lspName+"_forward", demandName+"_forward", lspBW)
                new_demand_for_LSP(plan, dest, src, lspName+"_reverse", demandName+"_reverse", lspBW)
            else:
                new_private_lsp(plan, src, dest, lspName, lspBW)
                new_demand_for_LSP(plan, src, dest, lspName, demandName, lspBW)


def new_demand_for_LSP(id, src, dest, lspName, demandName, val):
    serviceClass = 'Default'
    serviceClassMgr = id.getNetwork().getServiceClassManager()
    serviceClassExists = serviceClassMgr.hasServiceClass(
        ServiceClassKey(name=serviceClass))
    if not serviceClassExists:
        serviceClassRecord = ServiceClassRecord(name=serviceClass)
        serviceClassMgr.newServiceClass(serviceClassRecord)

    keylist = serviceClassMgr.getAllServiceClassKeys()
    dmdRec = DemandRecord(
        name=demandName,
        source=DemandEndpointKey(key=src),
        destination=DemandEndpointKey(key=dest),
        serviceClass=ServiceClassKey(name='Default'),
        privateLSP=LSPKey(
            name=lspName,
            sourceKey=NodeKey(name=src)
        )
    )
    dmdMgr = id.getNetwork().getDemandManager()
    dmdMgr.newDemand(dmdRec)

    dmdTraffKey = DemandTrafficKey(
        traffLvlKey=TrafficLevelKey(name='Default'),
        dmdKey=DemandKey(
            name=demandName,
            source=DemandEndpointKey(key=src),
            destination=DemandEndpointKey(key=dest),
            serviceClass=ServiceClassKey(name='Default'),
        )
    )
    dmdTrafficMgr = id.getTrafficManager().getDemandTrafficManager()
    dmdTrafficMgr.setTraffic(dmdTraffKey, val)
    traffic = dmdTrafficMgr.getTraffic(dmdTraffKey)
    print "traffic..."


def new_private_lsp(id, src, dest, name, lspBW):
    lspRec = LSPRecord(
        sourceKey=NodeKey(name=src),
        name=name,
        destinationKey=NodeKey(name=dest),
        isActive=True,
        isPrivate=True,
        setupBW=lspBW,
        type=LSPType.RSVP
    )
    lspMgr = id.getNetwork().getLSPManager()
    lspMgr.newLSP(lspRec)


def getnodename(loopback, nodelist):
    for node in nodelist:
        for k, v in node.items():
            if v == loopback:
                return k
