import com.cisco.wae.design
import logging


def createLsp(lspManager, lspIndex, sourceNodeKey, destinationNodeKey, lspBandwidth, directionText):
    lspRecord = com.cisco.wae.design.model.net.LSPRecord()
    lspRecord.sourceKey = sourceNodeKey
    # lspRecord.name = lspIndex + "(" + directionText + ")_flex_" + sourceNodeKey.name + "<->" + destinationNodeKey.name
    lspRecord.name = lspIndex
    lspRecord.destinationKey = destinationNodeKey
    lspRecord.setupBW = lspBandwidth
    lspRecord.isPrivate = True
    lspRecord.setupPriority = 0
    lspRecord.holdPriority = 0
    lsp = lspManager.newLSP(lspRecord)

    return lsp


def addPathToLsp(lsp, lspPathManager, namedPathManager, sourceNodeKey, pathOption, standby, active, primary_affinity, standby_affinity):
    # standby and active are booleans: True or False
    # pathOption is integer: i.e. 1 or 2
    lspRecord = lsp.getRecord()
    lspKey = lsp.getKey()

    if standby:
        standbyEnum = com.cisco.wae.design.model.net.LSPStandbyType.Standby
        affinity = standby_affinity
    else:
        standbyEnum = com.cisco.wae.design.model.net.LSPStandbyType.NotStandby
        affinity = primary_affinity

    namedPathRecord = com.cisco.wae.design.model.net.NamedPathRecord()
    namedPathRecord.sourceKey = sourceNodeKey
    namedPathRecord.name = lspRecord.name + "_" + str(pathOption)
    namedPath = namedPathManager.newNamedPath(namedPathRecord)
    namedPathKey = namedPath.getKey()

    lspPathRecord = com.cisco.wae.design.model.net.LSPPathRecord()
    lspPathRecord.lKey = lspKey
    lspPathRecord.npKey = namedPathKey
    lspPathRecord.pathOption = pathOption

    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    # print bin(int(affinity, scale))[2:].zfill(num_of_bits)
    affinitylist = list(bin(int(affinity, scale))[2:].zfill(num_of_bits))

    affinities = []
    c = 0
    for afbit in reversed(affinitylist):
        if afbit == '1':
            affinities.append(c)
        c += 1

    lspPath = lspPathManager.newLSPPath(lspPathRecord)
    lspPath.setActive(active)
    lspPath.setStandby(standbyEnum)
    lspPath.setIncludeAffinities(affinities)

    return lspPath


def lspStandbyToString(standby):
    if standby == com.cisco.wae.design.model.net.LSPStandbyType.Standby:
        standbyString = "Standby"
    else:
        if standby == com.cisco.wae.design.model.net.LSPStandbyType.NotStandby:
            standbyString = "not Standby"
        else:
            standbyString = "undefined"
    return standbyString


def printLspPathRoute(lspPath, routeSimulation, routeOptions):
    lspPathRouteRecord = routeSimulation.getLSPPathRouteRecord(lspPath, routeOptions)
    text = ""
    for interfaceKey in lspPathRouteRecord.interfaceUsage:
        text = text + interfaceKey.sourceKey.name + "(" + interfaceKey.name + ")   "
    return text


def printInterfaceList(interfaceList, route):
    text = ""
    for interfaceKey in interfaceList:
        if route:
            text = text + interfaceKey.sourceKey.name + "(" + interfaceKey.name + ")   "
        else:
            text = text + "(" + interfaceKey.name + ")" + interfaceKey.sourceKey.name + "   "
    return text


def calculateReverseNamedPathHopRecordList(lspPath, circuitManager):
    NamedPathHopRecordList = lspPath.getNamedPath().getHops()
    NamedPathHopRecordList.reverse()
    reverseInterfacePeerList = []
    for hopRecord in NamedPathHopRecordList:
        interfaceHop = hopRecord.ifaceHop
        reverseInterfacePeerList.append(interfaceHop)

    circuitRecords = circuitManager.getAllCircuitRecords()

    reverseInterfaceHopList = []
    for interfaceKey in reverseInterfacePeerList:
        for circuitRecord in circuitRecords:
            if circuitRecord.interfaceAKey == interfaceKey:
                reverseInterfaceHopList.append(circuitRecord.interfaceBKey)
            if circuitRecord.interfaceBKey == interfaceKey:
                reverseInterfaceHopList.append(circuitRecord.interfaceAKey)

    reverseNamedPathHopRecordList = []
    for interfaceHop in reverseInterfaceHopList:
        hopRecord = com.cisco.wae.design.model.net.NamedPathHopRecord()
        hopRecord.ifaceHop = interfaceHop
        hopRecord.type = com.cisco.wae.design.model.net.HopType.PathStrict
        reverseNamedPathHopRecordList.append(hopRecord)

    return reverseNamedPathHopRecordList

def buildNamedPathHopRecordList(lspPath, circuitManager, circuit_list):
    # namedPathHopRecordList = lspPath.getNamedPath().getHops()

    firstNode = lspPath.getLSP().getSource().getName()
    lastNode = lspPath.getLSP().getDestination().getName()

    circuitRecords = circuitManager.getAllCircuitRecords()

    hops = []
    for circuitRecord in circuitRecords:
        for circuit in circuit_list:
            circ_hops = []
            if circuitRecord.name == circuit:
                circ_hops.append(circuitRecord.interfaceAKey)
                circ_hops.append(circuitRecord.interfaceBKey)
                hops.append(circ_hops)

    ordered_hops = returnorderedlist(firstNode, lastNode,hops)
    if ordered_hops != None:
        namedPathHopRecordList = []
        for intf_hop in ordered_hops:
            hopRecord = com.cisco.wae.design.model.net.NamedPathHopRecord()
            hopRecord.ifaceHop = intf_hop
            hopRecord.type = com.cisco.wae.design.model.net.HopType.PathStrict
            namedPathHopRecordList.append(hopRecord)

        return namedPathHopRecordList
    else:
        return

def returnorderedlist(firstnode, lastnode, hops):
    hopsordered = []
    hopa = firstnode
    hopb = ""
    completed = False
    loopcount = 0
    while not completed:
        if len(hops) == 0: completed = True
        for hop in hops:
            if len(hop) != 2:
                logging.warn("Invalid hop!  Could not process hops!")
                return None
            elif hop[0].sourceKey.name == firstnode:
                hopsordered.append(hop[0])
                if hop[1].sourceKey.name != lastnode:
                    hopsordered.append(hop[1])
                    firstnode = hop[1].sourceKey.name
                hops.remove(hop)
                break
            elif hop[1].sourceKey.name == firstnode:
                hopsordered.append(hop[1])
                if hop[0].sourceKey.name != lastnode:
                    hopsordered.append(hop[0])
                    firstnode = hop[0].sourceKey.name
                hops.remove(hop)
                break
            elif loopcount > 200:
                logging.warn("Could not process hops!")
                return None
        loopcount += 1
    return hopsordered

def setStrictNamedPath(lspPath, NamedPathHopRecordList):
    # get named  path
    namedPath = lspPath.getNamedPath()

    # ensure named Path is empty
    namedPath.removeAllHops()

    # add Hops into Named Path
    namedPath.addHops(NamedPathHopRecordList)


def getRouteInterfaceList(lspPath, routeSimulation, routeOptions):
    lspPathRouteRecord = routeSimulation.getLSPPathRouteRecord(lspPath, routeOptions)
    routeInterfaceList = []
    routeInterfaceDoubleList = []
    for interfaceKey in lspPathRouteRecord.interfaceUsage:
        routeInterfaceList.append(interfaceKey)
        routeInterfaceDoubleList.append(lspPathRouteRecord.interfaceUsage[interfaceKey])

    return routeInterfaceList


def getHopInterfaceList(circuitManager, lspPath, routeSimulation, routeOptions):
    lspPathRouteRecord = routeSimulation.getLSPPathRouteRecord(lspPath, routeOptions)
    dynamicInterfaceList = []
    dynamicInterfaceDoubleList = []
    for interfaceKey in lspPathRouteRecord.interfaceUsage:
        dynamicInterfaceList.append(interfaceKey)
        dynamicInterfaceDoubleList.append(lspPathRouteRecord.interfaceUsage[interfaceKey])

    circuitRecords = circuitManager.getAllCircuitRecords()

    hopInterfaceList = []
    for interfaceKey in dynamicInterfaceList:
        #		print interfaceKey
        for circuitRecord in circuitRecords:
            if circuitRecord.interfaceAKey == interfaceKey:
                hopInterfaceList.append(circuitRecord.interfaceBKey)
            if circuitRecord.interfaceBKey == interfaceKey:
                hopInterfaceList.append(circuitRecord.interfaceAKey)

    return hopInterfaceList
