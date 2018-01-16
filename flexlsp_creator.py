import sys
import re
import os
import subprocess

sys.path.append("../")
import cs_common

import com.cisco.wae.design
from com.cisco.wae.design.model.net import NodeKey
# from com.cisco.wae.design.model.net import HopType

_FLAG_RE = re.compile(r'\A--?([-\w]+)\Z')
_HELP_RE = re.compile(r'\A-h(?:elp)?\Z', re.IGNORECASE)
_VERSION_RE = re.compile(r'\A-v(?:ersion)?\Z', re.IGNORECASE)

reportLogText = ""


def createflexlsp(options,conn,plan,nodes,index):
    '''
    main()
    '''

    #  get addon options
    # options = get_cli_options()
    #	print "[addon-print] options:", options
    #	print "[addon-print] plan-file:", options['plan-file']

    #	rprint("received Addon Options:")
    #	rprint(options)
    #	rprint("")

    #	rprint(options['nodes'])
    # with open(options['nodes']) as filehandle:
    #     rawNodeData = filehandle.read()
    #     filehandle.close()
    # #	rprint("raw Node Data:")
    # #	rprint(rawNodeData)
    # #	rprint("")
    # is_addon = 'CARIDEN_GUI' in os.environ

    # spin up WAE API instance
    # conn = com.cisco.wae.design.ServiceConnectionManager.newService()
    # plan = conn.getPlanManager().newPlanFromFileSystem(options['plan-file'])

    # get all necessary Managers
    network = plan.getNetwork()
    nodeManager = network.getNodeManager()
    circuitManager = network.getCircuitManager()

    lspManager = network.getLSPManager()
    lspPathManager = network.getLSPPathManager()
    namedPathManager = network.getNamedPathManager()

    simulationManager = conn.getSimulationManager()
    toolManager = conn.getToolManager()

    interfaceManager = network.getInterfaceManager()

    # find selected Nodes
    # nkl = nodeManager.getAllNodeKeys()
    newnkl = []
    for node in nodes:
        newnkl.append(NodeKey(node))

    nodeMap = nodeManager.getNodes(newnkl)
    # nodeMap = nodeManager.getNodesFromTable(rawNodeData)
    #	rprint("NodeMap:")
    #	rprint(nodeMap)

    nodeList = []
    nodeKeyList = []
    for nodeKey in nodeMap:
        nodeKeyList.append(nodeKey)
        nodeList.append(nodeMap[nodeKey])
    #	rprint("SourceNodeKey")
    #	rprint(nodeKeyList[0])
    #	rprint("SourceNode")
    #	rprint(nodeList[0])
    #	rprint("DestinationNodeKey")
    #	rprint(nodeKeyList[1])
    #	rprint("DestinationNode")
    #	rprint(nodeList[1])
    #	rprint("")

    rprint("Retrieved and parsed Options:")
    rprint("-----")
    rprint("")
    text = "LSP Endpoint A = " + nodeKeyList[0].name
    rprint(text)
    text = "LSP Endpoint B = " + nodeKeyList[1].name
    rprint(text)

    # lspIndex = options
    lspIndex = str(index)
    text = "LSP Index = " + str(lspIndex)
    rprint(text)

    sticky = options['sticky']
    if sticky:
        rprint("sticky enabled")

    coRouted = options['coRouted']
    if sticky:
        rprint("co-routing enabled")

    nonRevertive = options['nonRevertive']
    if sticky:
        rprint("non-revertive enabled")

    protection = options['protection']
    text = "Protection Mode = " + protection
    rprint(text)
    rprint("")

    lspBandwidth = 23

    # add the LSPs
    rprint("1. Creating forward LSP")
    lsp = cs_common.createLsp(lspManager, lspIndex, nodeKeyList[0], nodeKeyList[1], lspBandwidth, "Forward")
    text = "LSP called " + lsp.getName() + " with Bandwidth of " + str(
        lsp.getSetupBW()) + "Mbps created from Node " + lsp.getSource().getName() + " to Node " + lsp.getDestination().getName()
    rprint(text)

    # debug lsp2 begin
    # lsp2 = cs_common.createLsp(lspManager, str(99), nodeKeyList[0], nodeKeyList[1], 10, "Forward")
    # lsp2Path = cs_common.addPathToLsp(lsp2, lspPathManager, namedPathManager, nodeKeyList[0], 1, False, True)

    circuitRecords = circuitManager.getAllCircuitRecords()

    reverseInterfaceHopList = []
    for circuitRecord in circuitRecords:
        if circuitRecord.interfaceAKey.sourceKey.name == "4" and circuitRecord.interfaceBKey.sourceKey.name == "1":
            reverseInterfaceHopList.append(circuitRecord.interfaceAKey)
        if circuitRecord.interfaceBKey.sourceKey.name == "4" and circuitRecord.interfaceAKey.sourceKey.name == "1":
            reverseInterfaceHopList.append(circuitRecord.interfaceBKey)

    for circuitRecord in circuitRecords:
        if circuitRecord.interfaceAKey.sourceKey.name == "5" and circuitRecord.interfaceBKey.sourceKey.name == "4":
            reverseInterfaceHopList.append(circuitRecord.interfaceAKey)
        if circuitRecord.interfaceBKey.sourceKey.name == "5" and circuitRecord.interfaceAKey.sourceKey.name == "4":
            reverseInterfaceHopList.append(circuitRecord.interfaceBKey)

    for circuitRecord in circuitRecords:
        if circuitRecord.interfaceAKey.sourceKey.name == "3" and circuitRecord.interfaceBKey.sourceKey.name == "5":
            reverseInterfaceHopList.append(circuitRecord.interfaceAKey)
        if circuitRecord.interfaceBKey.sourceKey.name == "3" and circuitRecord.interfaceAKey.sourceKey.name == "5":
            reverseInterfaceHopList.append(circuitRecord.interfaceBKey)

    reverseNamedPathHopRecordList = []
    for interfaceHop in reverseInterfaceHopList:
        hopRecord = com.cisco.wae.design.model.net.NamedPathHopRecord()
        hopRecord.ifaceHop = interfaceHop
        hopRecord.type = com.cisco.wae.design.model.net.HopType.PathStrict
        reverseNamedPathHopRecordList.append(hopRecord)

    # cs_common.setStrictNamedPath(lsp2Path, reverseNamedPathHopRecordList)
    # rprint("lsp2")
    # rprint(reverseNamedPathHopRecordList)
    # debug lsp2 end

    rprint("")
    rprint("---")
    rprint("")

    rprint("2. Creating Reverse LSP")
    rlsp = cs_common.createLsp(lspManager, lspIndex, nodeKeyList[1], nodeKeyList[0], lspBandwidth, "Reverse")
    text = "LSP called " + rlsp.getName() + " with Bandwidth of " + str(
        rlsp.getSetupBW()) + "Mbps created from Node " + rlsp.getSource().getName() + " to Node " + rlsp.getDestination().getName()
    rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    # add dynamic forward LSP Paths
    rprint("3. Adding dynamic Forward Paths")
    workingLspPath = cs_common.addPathToLsp(lsp, lspPathManager, namedPathManager, nodeKeyList[0], 1, False, True)
    protectLspPath = cs_common.addPathToLsp(lsp, lspPathManager, namedPathManager, nodeKeyList[0], 2, True, True)
    standbyString = cs_common.lspStandbyToString(workingLspPath.getStandby())
    text = "working LSP using path-option " + str(
        workingLspPath.getPathOption()) + " with named Path " + workingLspPath.getNamedPath().getName() + " created (" + standbyString + ")"
    rprint(text)
    standbyString = cs_common.lspStandbyToString(protectLspPath.getStandby())
    text = "protect LSP using path-option " + str(
        protectLspPath.getPathOption()) + " with named Path " + protectLspPath.getNamedPath().getName() + " created (" + standbyString + ")"
    rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    # run simulation
    rprint("4. Running Simulation")
    failureScenarioRecord = com.cisco.wae.design.sim.FailureScenarioRecord()
    routeSimulation = simulationManager.newRouteSimulation(plan, failureScenarioRecord)
    routeOptions = com.cisco.wae.design.sim.RouteOptions()
    lspRouteRecords = routeSimulation.getAllLSPRouteRecords(routeOptions)
    lspPathRouteRecords = routeSimulation.getAllLSPPathRouteRecords(routeOptions)

    # retrieve and print dynamic forward Paths
    rprint("working forward LSP Path:")
    indent = " "
    workingRouteInterfaceList = cs_common.getRouteInterfaceList(workingLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(workingRouteInterfaceList, True)
    text = indent + text
    rprint(text)
    rprint("protect forward LSP Path:")
    indent = " "
    protectRouteInterfaceList = cs_common.getRouteInterfaceList(protectLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(protectRouteInterfaceList, True)
    text = indent + text
    rprint(text)

    # debug lsp2
    # rprint("lsp2")
    # lsp2InterfaceList = cs_common.getRouteInterfaceList(lsp2Path, routeSimulation, routeOptions)
    # text = cs_common.printInterfaceList(lsp2InterfaceList, True)
    # text = indent + text
    # rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    rprint("5. Disjoint Optimizer")
    disjointOptimizer = toolManager.newLSPDisjointPathOptimizer()
    disjointOptimizerOptions = com.cisco.wae.design.tools.LSPDisjointPathOptimizerOptions()
    lspList = [lsp.getKey()]
    disjointOptimizerOptions.lsps = lspList
    disjointOptimizerResults = disjointOptimizer.run(network, disjointOptimizerOptions)

    rprint("")
    rprint("---")
    rprint("")

    rprint("6. Simulate again after adding explicit Paths to Forward LSPs")
    failureScenarioRecord = com.cisco.wae.design.sim.FailureScenarioRecord()
    routeSimulation = simulationManager.newRouteSimulation(plan, failureScenarioRecord)
    routeOptions = com.cisco.wae.design.sim.RouteOptions()
    lspRouteRecords = routeSimulation.getAllLSPRouteRecords(routeOptions)
    lspPathRouteRecords = routeSimulation.getAllLSPPathRouteRecords(routeOptions)

    # retrieve and print optimized forward Paths
    rprint("disjoint optimized and sticky working forward LSP Path:")
    indent = " "
    workingRouteInterfaceList = cs_common.getRouteInterfaceList(workingLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(workingRouteInterfaceList, True)
    text = indent + text
    rprint(text)
    rprint("disjoint optimized and sticky protect forward LSP Path:")
    indent = " "
    protectRouteInterfaceList = cs_common.getRouteInterfaceList(protectLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(protectRouteInterfaceList, True)
    text = indent + text
    rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    # adding sticky, co-routed reverse paths
    rprint("7. Calculating and adding co-routed & sticky reverse Paths")

    # add paths to reverse LSP
    rWorkingLspPath = cs_common.addPathToLsp(rlsp, lspPathManager, namedPathManager, nodeKeyList[1], 1, False, True)
    rProtectLspPath = cs_common.addPathToLsp(rlsp, lspPathManager, namedPathManager, nodeKeyList[1], 2, True, True)

    # calculate reverse paths to be used
    workingReverseNamedPathHopRecordList = cs_common.calculateReverseNamedPathHopRecordList(workingLspPath,
                                                                                            circuitManager)
    protectReverseNamedPathHopRecordList = cs_common.calculateReverseNamedPathHopRecordList(protectLspPath,
                                                                                            circuitManager)

    # set explicit hops
    cs_common.setStrictNamedPath(rWorkingLspPath, workingReverseNamedPathHopRecordList)
    cs_common.setStrictNamedPath(rProtectLspPath, protectReverseNamedPathHopRecordList)

    # recompute simulation
    #	routeSimulation.recompute()
    failureScenarioRecord = com.cisco.wae.design.sim.FailureScenarioRecord()
    routeSimulation = simulationManager.newRouteSimulation(plan, failureScenarioRecord)
    routeOptions = com.cisco.wae.design.sim.RouteOptions()
    lspRouteRecords = routeSimulation.getAllLSPRouteRecords(routeOptions)
    lspPathRouteRecords = routeSimulation.getAllLSPPathRouteRecords(routeOptions)

    # rertrieve and print paths
    rprint("co-routing and sticky working reverse LSP Path:")
    indent = " "
    rWorkingRouteInterfaceList = cs_common.getRouteInterfaceList(rWorkingLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(rWorkingRouteInterfaceList, True)
    text = indent + text
    rprint(text)
    rprint("co-routing and sticky protect reverse LSP Path:")
    indent = " "
    rProtectRouteInterfaceList = cs_common.getRouteInterfaceList(rProtectLspPath, routeSimulation, routeOptions)
    #	rprint("route interface list")
    #	rprint(rProtectRouteInterfaceList)
    text = cs_common.printInterfaceList(rProtectRouteInterfaceList, True)
    text = indent + text
    rprint(text)

    rprint("")
    rprint("hops")
    rprint(rProtectLspPath.getNamedPath().getHops())
    rprint("")
    #	rprint("ifusage")
    #	rprint(routeSimulation.getLSPPathRouteRecord(rProtectLspPath, routeOptions).interfaceUsage)

    rprint("")
    rprint("---")
    rprint("")

    # create report
    rprint("8. Creating Report")
    reportManager = network.getReportManager()
    reportKeyName = "FlexLSP Creator"

    textReportList = []
    textSection = com.cisco.wae.design.model.net.ReportTextSection(title='Log', content=reportLogText, displayIndex=1)
    textReportList.append(textSection)

    reportKey = com.cisco.wae.design.model.net.ReportKey(reportKeyName)
    if reportManager.hasReport(reportKey):
        reportManager.removeReport(reportKey)

    reportRecord = com.cisco.wae.design.model.net.ReportRecord(name=reportKeyName, textSections=textReportList)
    newReport = reportManager.newReport(reportRecord)

    # if is_addon:
    #     generate_return_config_file(options, reportKeyName)

    # save the new plan-file with the created report
    # try:
    #     plan.serializeToFileSystem(options['out-file'])
    # except Exception as exception:
    #     sys.stderr.write("Fatal[0]: Unable to write: " + options['out-file'] + " (" + exception.reason + ")\n")
    #     sys.exit(1)
    #
    # return 0


# do not need anymore?

def do_not_need():
    # run simulation
    rprint("6. Running Simulation again")
    failureScenarioRecord = com.cisco.wae.design.sim.FailureScenarioRecord()
    routeSimulation = simulationManager.newRouteSimulation(plan, failureScenarioRecord)
    routeOptions = com.cisco.wae.design.sim.RouteOptions()
    lspRouteRecords = routeSimulation.getAllLSPRouteRecords(routeOptions)
    lspPathRouteRecords = routeSimulation.getAllLSPPathRouteRecords(routeOptions)

    # retrieve dynamic forward Paths
    rprint("working forward LSP Path:")
    indent = " "
    workingRouteInterfaceList = cs_common.getRouteInterfaceList(workingLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(workingRouteInterfaceList, True)
    text = indent + text
    rprint(text)
    rprint("protect forward LSP Path:")
    indent = " "
    lspPathRouteRecord = routeSimulation.getLSPPathRouteRecord(protectLspPath, routeOptions)
    #	rprint(lspPathRouteRecord)
    protectRouteInterfaceList = cs_common.getRouteInterfaceList(protectLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(protectRouteInterfaceList, True)
    text = indent + text
    rprint(text)
    #	rprint(protectLspPath.getNamedPath().getHops())

    rprint("")
    rprint("---")
    rprint("")

    # calculating reverse path
    rprint("7. Calculating explicit&sticky Reverse Paths")
    rprint("working LSP Path:")
    rprint("---")
    rWorkingHopInterfaceHopList = workingRouteInterfaceList
    rWorkingHopInterfaceHopList.reverse()
    indent = " "
    text = cs_common.printInterfaceList(rWorkingHopInterfaceHopList, False)
    text = indent + text
    rprint(text)
    rprint("protect LSP Path:")
    rProtectHopInterfaceHopList = protectRouteInterfaceList
    rProtectHopInterfaceHopList.reverse()
    indent = " "
    text = cs_common.printInterfaceList(rProtectHopInterfaceHopList, False)
    text = indent + text
    rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    # calculate explicit forward paths
    rprint("5. Calculating sticky forward Paths")
    rprint("working LSP Path:")
    workingHopInterfaceHopList = cs_common.getHopInterfaceList(circuitManager, workingLspPath, routeSimulation,
                                                               routeOptions)
    indent = " "
    text = cs_common.printInterfaceList(workingHopInterfaceHopList, False)
    text = indent + text
    rprint(text)
    rprint("protect LSP Path:")
    protectHopInterfaceHopList = cs_common.getHopInterfaceList(circuitManager, protectLspPath, routeSimulation,
                                                               routeOptions)
    indent = " "
    text = cs_common.printInterfaceList(protectHopInterfaceHopList, False)
    text = indent + text
    rprint(text)

    rprint("")
    rprint("---")
    rprint("")

    rprint("7. Calculating co-routed & sticky reverse Paths")
    rprint("calculating reverse working")
    #	rprint(workingReverseNamedPathHopRecordList)
    indent = " "
    workingRouteInterfaceList = cs_common.getRouteInterfaceList(workingLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(workingRouteInterfaceList, True)
    text = indent + text
    rprint(text)

    rprint("calculating reverse protect")
    #	rprint(protectReverseNamedPathHopRecordList)
    indent = " "
    lspPathRouteRecord = routeSimulation.getLSPPathRouteRecord(protectLspPath, routeOptions)
    #	rprint(lspPathRouteRecord)
    protectRouteInterfaceList = cs_common.getRouteInterfaceList(protectLspPath, routeSimulation, routeOptions)
    text = cs_common.printInterfaceList(protectRouteInterfaceList, True)
    text = indent + text
    rprint(text)


# do not need end

def rprint(input):
    print input

# def rprint(input):
#     global reportLogText
#     reportLogText = reportLogText + str(input) + "\n"


# def get_cli_options():
#     '''
#         Captures and validates the CLI options
#     '''
#     options = process_argv()
#     # options = validate_options(options)
#     return options
#
#
# def process_argv():
#     '''
#         Returns the cli arguments in a dictionary
#     '''
#     argv = list(sys.argv)
#     options = {}
#     argv.pop(0)
#     while len(argv) > 0:
#         item = argv.pop(0)
#         next_item = argv.pop(0)
#         options[re.sub(r'^-', '', item)] = next_item
#     return options


# def validate_options(options):
#     '''
#         Validates the CLI options
#     '''
#     # Ensure we fill out any defined defaults
#     for option in valid_options.keys():
#         if 'default' in valid_options[option]:
#             default = valid_options[option]['default']
#             option = re.sub(r'^-', '', option)
#             if option not in options:
#                 options[option] = default
#
#     # Ensure we check our allowed values
#     for option in valid_options.keys():
#         if 'allowed' in valid_options[option]:
#             allowed_values = valid_options[option]['allowed']
#             option = re.sub(r'^-', '', option)
#             if option in options:
#                 if options[option] not in allowed_values:
#                     do_help()
#
#     # Ensure we have our required options
#     for option in valid_options.keys():
#         if 'REQUIRED' in valid_options[option]:
#             if valid_options[option]['REQUIRED'] == 1:
#                 option = re.sub(r'^-', '', option)
#                 if option not in options:
#                     do_help()
#
#     return options


# def generate_return_config_file(options, reportKey):
#     '''
#         Generate a return-config-file so the WAE GUI will display the report
#     '''
#     with open(options['return-config-file'], "w") as filehandle:
#         filehandle.write("<AddOnReturnConfig>\n")
#         filehandle.write("Property\tValue\n")
#         filehandle.write("ShowReport\t" + reportKey + "\n")
#         filehandle.close()
#     return


# if __name__ == '__main__':
#     try:
#         sys.exit(main())
#     except Exception as exception:
#         import traceback
#
#         print traceback.print_exc()
#         sys.stderr.write('Fatal [0]: ' + str(exception) + '\n')
