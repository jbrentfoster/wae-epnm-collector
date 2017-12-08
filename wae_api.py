import os

oldPATH = os.getenv('PATH')
newPATH = oldPATH + ";" + "C:\Users\\brfoster\Desktop\DesktopSweep.2016.05.25\SDN\Cariden\WAE-Design-k9-6.4.10-Windows-x86_64\lib\exec"
os.environ['PATH'] = newPATH
# print "PYTHONPATH=" + os.getenv('PYTHONPATH')
# print "PATH=" + os.getenv('PATH')
# print "CARDEN_HOME=" + os.getenv('CARIDEN_HOME')
import com.cisco.wae.design
import waecode.planbuild
import json


def main():
    # Create a service to be used by this script
    conn = com.cisco.wae.design.ServiceConnectionManager.newService()

    cwd = os.getcwd()
    fileName = os.path.join(cwd, 'planfiles/blank.pln')
    plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

    with open("jsonfiles/l1Nodes.json", 'rb') as f:
        l1nodesdict = json.load(f)
        f.close()

    l1nodes = []
    for k1, v1 in l1nodesdict.items():
        l1nodes.append(v1['Name'])

    waecode.planbuild.generateL1nodes(plan, l1nodelist=l1nodes)

    with open("jsonfiles/l1Links.json", 'rb') as f:
        l1linksdict = json.load(f)
        f.close()

    l1links = []
    for k1, v1 in l1linksdict.items():
        l1links.append(v1['Nodes'])

    waecode.planbuild.generateL1links(plan, l1linklist=l1links)

    with open("jsonfiles/l3Links_reordered_l1hops.json", 'rb') as f:
        l3linksdict = json.load(f)
        f.close()

    l3nodes = []
    for k1, v1 in l3linksdict.items():
        l3nodes.append(k1)

    waecode.planbuild.generateL3nodes(plan, l3nodes)

    c = 0
    i = 0
    linkslist = []
    duplicatelink = False
    for k1, v1 in l3linksdict.items():
        firstnode = k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    print "***************Linkname is: " + k3
                    firstl1node = ""
                    lastl1node = ""
                    l1hops = []
                    lastnode = v3.get('Neighbor')
                    discoveredname = v3.get('discoveredname')
                    rsvpbw = float(v3.get('RSVP BW').split(' ')[0])
                    for linkdiscoveredname in linkslist:
                        if discoveredname == linkdiscoveredname: duplicatelink = True
                    if 'Ordered L1 Hops' in v3 and not duplicatelink:
                        if len(v3.get('Ordered L1 Hops')) > 0:
                            linkslist.append(discoveredname)
                            c += 1
                            i += 1
                            for l1hop in v3.get('Ordered L1 Hops'):
                                nodelist = []
                                firstlasthop = False
                                for k5, v5 in l1hop.get('Nodes').items():
                                    if k5 == firstnode or k5 == lastnode: firstlasthop = True
                                    nodelist.append(k5)
                                if not firstlasthop:
                                    l1hops.append(nodelist)
                                elif nodelist[0] == firstnode:
                                    firstl1node = nodelist[1]
                                elif nodelist[1] == firstnode:
                                    firstl1node = nodelist[0]
                                elif nodelist[0] == lastnode:
                                    lastl1node = nodelist[1]
                                elif nodelist[1] == lastnode:
                                    lastl1node = nodelist[0]
                            name = "L1_circuit_" + str(c)
                            l1circuit = waecode.planbuild.generateL1circuit(plan, name, firstl1node, lastl1node, l1hops,
                                                                            rsvpbw)
                            name = "L3_circuit_" + str(i)
                            l3circuit = waecode.planbuild.generateL3circuit(plan, name, firstnode, lastnode)
                            l3circuit.setL1Circuit(l1circuit)
                            l3circuit.setCapacity(l1circuit.getBandwidth())
                    elif not duplicatelink:
                        i += 1
                        name = "L3_circuit_" + str(i)
                        linkslist.append(discoveredname)
                        l3circuit = waecode.planbuild.generateL3circuit(plan, name, firstnode, lastnode)
                        l3circuit.setCapacity(rsvpbw)

                    duplicatelink = False

    plan.serializeToFileSystem('planfiles/test.pln')
    print "done"


if __name__ == '__main__':
    main()



    # intfAkey = InterfaceKey(name = 'FOO-L3-intf', sourceKey = nodeAKey)
    # intfBkey = InterfaceKey(name='BAR-L3-intf', sourceKey=nodeBKey)
    # circRec = CircuitRecord(name='L3-FOO-to-BAR',interfaceAKey=intfAkey,interfaceBKey=intfBkey)

    # circuitManager = plan.getNetwork().getCircuitManager()
    # circKey = circuitManager.newCircuitKey(intfAkey,intfBkey)
    # circ = circuitManager.getCircuit(circKey)

    # Check for the existence of a few nodes
    # for nodeName in ['cr1.ams', 'cr7.ams', 'er1.lon', 'er1.nyc']:
    #     nodeKey = com.cisco.wae.design.model.net.NodeKey(name=nodeName)
    #     if plan.getNetwork().getNodeManager().hasNode(nodeKey):
    #         print('Network contains node ' + nodeName)
    #     else:
    #         print('Network does not contain node ' + nodeName)

    # l1nodekeys = l1NodeManager.getAllL1NodeKeys()
    # l1nodeAKey = l1nodekeys[0]
    # l1nodeBKey = l1nodekeys[1]

    # l1nodeAKey = L1NodeKey('L1-FOO')
    # l1nodeBKey = L1NodeKey('L1-BAR')



    # l1NodeManager = plan.getNetwork().getL1Network().getL1NodeManager()
    #
    # l1nodeRec = L1NodeRecord(name="L1-FOO")
    # l1NodeManager.newL1Node(l1nodeRec)
    #
    # l1nodeRec = L1NodeRecord(name="L1-BAR")
    # l1NodeManager.newL1Node(l1nodeRec)
