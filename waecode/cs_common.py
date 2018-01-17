import com.cisco.wae.design


def createLsp(lspManager, lspIndex, sourceNodeKey, destinationNodeKey, lspBandwidth, directionText):
    lspRecord = com.cisco.wae.design.model.net.LSPRecord()
    lspRecord.sourceKey = sourceNodeKey
    # lspRecord.name = lspIndex + "(" + directionText + ")_flex_" + sourceNodeKey.name + "<->" + destinationNodeKey.name
    lspRecord.name = lspIndex
    lspRecord.destinationKey = destinationNodeKey
    lspRecord.setupBW = lspBandwidth
    lspRecord.isPrivate = True
    lsp = lspManager.newLSP(lspRecord)

    return lsp


def addPathToLsp(lsp, lspPathManager, namedPathManager, sourceNodeKey, pathOption, standby, active):
    # standby and active are booleans: True or False
    # pathOption is integer: i.e. 1 or 2
    lspRecord = lsp.getRecord()
    lspKey = lsp.getKey()

    if standby:
        standbyEnum = com.cisco.wae.design.model.net.LSPStandbyType.Standby
    else:
        standbyEnum = com.cisco.wae.design.model.net.LSPStandbyType.NotStandby

    namedPathRecord = com.cisco.wae.design.model.net.NamedPathRecord()
    namedPathRecord.sourceKey = sourceNodeKey
    namedPathRecord.name = lspRecord.name + "_" + str(pathOption)
    namedPath = namedPathManager.newNamedPath(namedPathRecord)
    namedPathKey = namedPath.getKey()

    lspPathRecord = com.cisco.wae.design.model.net.LSPPathRecord()
    lspPathRecord.lKey = lspKey
    lspPathRecord.npKey = namedPathKey
    lspPathRecord.pathOption = pathOption

    lspPath = lspPathManager.newLSPPath(lspPathRecord)
    lspPath.setActive(active)
    lspPath.setStandby(standbyEnum)

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