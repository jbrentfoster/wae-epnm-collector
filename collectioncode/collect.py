import collectioncode.utils
import time
import re
import json
import logging
import sys
from multiprocessing.dummy import Pool as ThreadPool
import wae_api
from get_4k_seed_nodes import run_get_4k_seed_nodes, get_potential_seednode, get_random_nodes_for_states



def collection_router(collection_call):
    if collection_call['type'] == "l1nodes":
        logging.info("Collecting L1 nodes...")
        collectL1Nodes_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
    if collection_call['type'] == "l1links":
        logging.info("Collecting L1 links...")
        collectL1links_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
    if collection_call['type'] == 'allnodes':
        logging.info("Collection all node equipment details...")
        collectAllNodes_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
    if collection_call['type'] == '4knodes':
        logging.info("Collecting 4k nodes...")
        collect4kNodes_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
    if collection_call['type'] == "lsps":
        logging.info("Collecting LSPs...")
        collectlsps_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
    if collection_call['type'] == "mpls":
        logging.info("Collecting 4k nodes...")
        collect4kNodes_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'])
        logging.info("Collecting MPLS topological links...")
        collect_mpls_links_json(collection_call['baseURL'], collection_call['epnmuser'],
                                       collection_call['epnmpassword'])
        logging.info("Collecting MPLS nodes...")
        collectMPLSnodes()
        logging.info("Collecting MPLS topology...")
        collect_mpls_topo_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'],
                               collection_call['state_or_states'])
        logging.info("Collecting ISIS hostnames...")
        collect_hostnames_json(collection_call['baseURL'], collection_call['epnmuser'], collection_call['epnmpassword'],
                               collection_call['state_or_states'])
        process_hostnames(collection_call['state_or_states'])
        logging.info("Processing MPLS topology...")
        processMPLS(collection_call['state_or_states'])

        logging.info("Adding MPLS TL data to L3 links...")
        try:
            add_mpls_tl_data(collection_call['baseURL'], collection_call['epnmuser'],
                                       collection_call['epnmpassword'], collection_call['state_or_states'])
        except Exception as err:
            logging.critical("MPLS topological links are not valid.  Halting execution.")
            sys.exit("Collection error.  Halting execution.")

        logging.info("Collecting L3 link termination points...")
        collect_termination_points_threaded(collection_call['baseURL'], collection_call['epnmuser'],
                                                collection_call['epnmpassword'], collection_call['state_or_states'])

        logging.info("Collecting optical virtual connections...")
        collectvirtualconnections_json(collection_call['baseURL'], collection_call['epnmuser'],
                                       collection_call['epnmpassword'])
        logging.info("Adding vc-fdn to L3links...")
        add_vcfdn_l3links(collection_call['state_or_states'])

    if collection_call['type'] == "optical":
        logging.info("Collecting optical virtual connections...")
        collectvirtualconnections_json(collection_call['baseURL'], collection_call['epnmuser'],
                                       collection_call['epnmpassword'])
        logging.info("Parsing OCH-trails...")
        parse_vc_optical_och_trails()

        logging.info("Getting OCH-trails wavelengths...")
        add_wavelength_vc_optical_och_trails()

        logging.info("Collection OTU links...")
        collect_otu_links_json(collection_call['baseURL'], collection_call['epnmuser'],
                               collection_call['epnmpassword'])

        logging.info("Collecting OTU termination points...")
        collect_otu_termination_points_threaded(collection_call['baseURL'], collection_call['epnmuser'],
                                                collection_call['epnmpassword'])

        logging.info("Adding OCH trails to OTU links...")
        add_och_trails_to_otu_links()

        logging.info("Collecting L1 paths for OCH-trails...")
        addL1hopstoOCHtrails_threaded(collection_call['baseURL'], collection_call['epnmuser'],
                                                collection_call['epnmpassword'])
        logging.info("Re-ordering L1 hops for OCH-trails...")
        reorderl1hops_och_trails()
        logging.info("Parsing OTN links from OTU link data...")
        parse_otn_links()
        logging.info("Parsing ODU services from vc-optical data...")
        parse_odu_services()
        logging.info("Getting multi-layer routes for OTN services...")
        collect_multilayer_route_odu_services_threaded(collection_call['baseURL'], collection_call['epnmuser'],
                                                collection_call['epnmpassword'])
    


def runcollector(baseURL, epnmuser, epnmpassword, state_or_states):
    # ##  "l1nodes":
    # logging.info("Collecting L1 nodes...")
    # collectL1Nodes_json(baseURL, epnmuser, epnmpassword)
    # ##  "l1links":
    # logging.info("Collecting L1 links...")
    # collectL1links_json(baseURL, epnmuser, epnmpassword)
    # ## 'allnodes':
    # logging.info("Collection all node equipment details...")
    # collectAllNodes_json(baseURL, epnmuser, epnmpassword)
    # ##  '4knodes':
    # logging.info("Collecting 4k nodes...")
    # collect4kNodes_json(baseURL, epnmuser, epnmpassword)
    ##   "lsps":
    # logging.info("Collecting LSPs...")
    # collectlsps_json(baseURL, epnmuser, epnmpassword)
    ## "mpls":
    logging.info("Collecting 4k nodes...")
    collect4kNodes_json(baseURL, epnmuser, epnmpassword)
    logging.info("Collecting MPLS topological links...")
    collect_mpls_links_json(baseURL, epnmuser, epnmpassword)
    # logging.info("Collecting MPLS nodes...")
    # collectMPLSnodes()
    logging.info("Collecting MPLS topology...")
    collect_mpls_topo_json(baseURL, epnmuser, epnmpassword,
                            state_or_states)
    logging.info("Collecting ISIS hostnames...")
    collect_hostnames_json(baseURL, epnmuser, epnmpassword,
                            state_or_states)
    process_hostnames(state_or_states)
    logging.info("Processing MPLS topology...")
    processMPLS(state_or_states)

    logging.info("Adding MPLS TL data to L3 links...")
    try:
        add_mpls_tl_data(baseURL, epnmuser, epnmpassword, state_or_states)
    except Exception as err:
        logging.critical("MPLS topological links are not valid.  Halting execution.")
        sys.exit("Collection error.  Halting execution.")
    #
    # logging.info("Collecting L3 link termination points...")
    # collect_termination_points_threaded(baseURL, epnmuser,
    #                                         epnmpassword, state_or_states)
    #
    # logging.info("Collecting optical virtual connections...")
    # collectvirtualconnections_json(baseURL, epnmuser,
    #                                 epnmpassword)
    # logging.info("Adding vc-fdn to L3links...")
    # add_vcfdn_l3links(state_or_states)



def collectL1Nodes_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-physical:node?product-series=Cisco Network Convergence System 2000 Series&.depth=1&.startIndex=" + str(
            startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/l1-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


    with open("jsongets/l1-nodes.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    l1nodes = {}
    i = 1
    for node in thejson['com.response-message']['com.data']['nd.node']:
        if node.get('nd.product-series') == "Cisco Network Convergence System 2000 Series":
            nodeName = node.get('nd.name')
            logging.info("Processing node " + nodeName)
            try:
                latitude = node.get('nd.latitude')
                longitude = node.get('nd.longitude')
            except KeyError:
                logging.error(
                    "Could not get longitude or latitidude for node " + nodeName + ".  Setting to 0.0 and 0.0")
                latitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
                longitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
            l1nodes['Node' + str(i)] = dict([('Name', nodeName), ('Latitude', latitude), ('Longitude', longitude)])
            i += 1

    with open("jsonfiles/l1Nodes.json", 'wb') as f:
        f.write(json.dumps(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))


def collectL1links_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer&.startIndex=" + str(
            startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/l1-links.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsongets/l1-links.json", 'rb') as f:
        jsonresponse = f.read()

    thejson = json.loads(jsonresponse)

    l1links = {}
    i = 1
    for link in thejson.get('com.response-message').get('com.data').get('topo.topological-link'):
        fdn = link.get('topo.fdn')
        discovered_name = link.get('topo.discovered-name')
        nodes = []
        try:
            endpointlist = link.get('topo.endpoint-list').get('topo.endpoint')
        except Exception as err:
            logging.warn("L1 Link missing valid endpoint-list " + fdn + " ...removing this link from L1 topology.")
            continue
        logging.info("Processing L1 link " + fdn)
        if len(endpointlist) > 1 and isinstance(endpointlist, list) and 'WDMSIDE' in discovered_name:
            for ep in endpointlist:
                endpoint = ep.get('topo.endpoint-ref')
                node = endpoint.split('!')[1].split('=')[1]
                nodes.append(node)
            if len(nodes) > 1:
                duplicates = False
                if not duplicates:
                    l1links['Link' + str(i)] = dict([('fdn', fdn)])
                    l1links['Link' + str(i)]['Nodes'] = nodes
                i += 1

    with open("jsonfiles/l1Links.json", 'wb') as f:
        f.write(json.dumps(l1links, f, sort_keys=True, indent=4, separators=(',', ': ')))


def collectAllNodes_json_new(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-resource-physical:node?.depth=1"
    jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
    jsonaddition = json.loads(jsonresponse)

    with open("jsongets/all-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonaddition, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsongets/all-nodes.json", 'rb') as f:
        jsonresponse = f.read()

    thejson = json.loads(jsonresponse)

    nodes = []
    # i = 1
    for node in thejson.get('com.response-message').get('com.data').get('nd.node'):
        # if node['nd.product-series'] == "Cisco Network Convergence System 2000 Series":
        try:
            node_fdn = node.get('nd.fdn')
            nodeName = node.get('nd.name')
            logging.info("Processing for equipment information " + nodeName)
            product_type = node.get('nd.product-type')
            software_version = node.get('nd.software-version')
            management_address = node.get('nd.management-address')
            description = node.get('nd.description')
            nodes.append({'name': nodeName, 'product-type': product_type, 'software-version': software_version,
                            'management-address': management_address, 'description': description})
        except Exception as err:
            logging.warn("Node equipment details could not be retrieved!  " + node_fdn)
        # i += 1

    with open("jsonfiles/all-nodes.json", 'wb') as f:
        f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        
        
def collectAllNodes_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-physical:node?.depth=1&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/all-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsongets/all-nodes.json", 'rb') as f:
        jsonresponse = f.read()


    thejson = json.loads(jsonresponse)

    nodes = []
    # i = 1
    with open("jsonfiles/all-nodes.json", 'wb') as f:
        for node in thejson['com.response-message']['com.data']['nd.node']:
            # if node['nd.product-series'] == "Cisco Network Convergence System 2000 Series":
            try:
                node_fdn = node['nd.fdn']
                nodeName = node['nd.name']
                logging.info("Processing for equipment information " + nodeName)
                product_type = node['nd.product-type']
                software_version = node['nd.software-version']
                management_address = node['nd.management-address']
                description = node['nd.description']
                nodes.append({'name': nodeName, 'product-type': product_type, 'software-version': software_version,
                              'management-address': management_address, 'description': description})
            except Exception as err:
                logging.warn("Node equipment details could not be retrieved!  " + node_fdn)
            # i += 1
        f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

        
def collect4kNodes_json_new(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-resource-physical:node?product-series=Cisco Network Convergence System 4000 Series"
    jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
    jsonaddition = json.loads(jsonresponse)

    with open("jsongets/4k-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonaddition, f, sort_keys=True, indent=4, separators=(',', ': ')))


    with open("jsongets/4k-nodes.json", 'rb') as f:
        jsonresponse = f.read()


    thejson = json.loads(jsonresponse)

    l1nodes = {}
    i = 1
    for node in thejson['com.response-message']['com.data']['nd.node']:
        if node['nd.product-series'] == "Cisco Network Convergence System 4000 Series":
            nodeName = node['nd.name']
            fdn = node['nd.fdn']
            logging.info("Processing node " + nodeName)
            try:
                latitude = node['nd.latitude']
                longitude = node['nd.longitude']
            except KeyError:
                logging.error(
                    "Could not get longitude or latitidude for node " + nodeName + ".  Setting to 0.0 and 0.0")
                latitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
                longitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
            l1nodes['Node' + str(i)] = dict(
                [('Name', nodeName), ('fdn', fdn), ('Latitude', latitude), ('Longitude', longitude)])
            i += 1
        # f.write(json.dumps(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsonfiles/4k-nodes_db.json", 'wb') as f:
        json.dump(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': '))
        
        
def collect4kNodes_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-physical:node?product-series=Cisco Network Convergence System 4000 Series&.startIndex=" + str(
            startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/4k-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsongets/4k-nodes.json", 'rb') as f:
        jsonresponse = f.read()


    thejson = json.loads(jsonresponse)

    l1nodes = {}
    i = 1
    for node in thejson['com.response-message']['com.data']['nd.node']:
        if node['nd.product-series'] == "Cisco Network Convergence System 4000 Series":
            nodeName = node['nd.name']
            fdn = node['nd.fdn']
            logging.info("Processing node " + nodeName)
            try:
                latitude = node['nd.latitude']
                longitude = node['nd.longitude']
            except KeyError:
                logging.error(
                    "Could not get longitude or latitidude for node " + nodeName + ".  Setting to 0.0 and 0.0")
                latitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
                longitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
            l1nodes['Node' + str(i)] = dict(
                [('Name', nodeName), ('fdn', fdn), ('Latitude', latitude), ('Longitude', longitude)])
            i += 1
        # f.write(json.dumps(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsonfiles/4k-nodes_db.json", 'wb') as f:
        json.dump(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': '))


def collect_mpls_topo_json(baseURL, epnmuser, epnmpassword, state_or_states):
    with open("collectioncode/post-cli-template-mpls.json", 'r') as f:
        jsonbody = f.read()

    jsonbody_js = json.loads(jsonbody)
    ## Get Seed Nodes Based on State or States (New York, Flordia)
    run_get_4k_seed_nodes()
    get_potential_seednode(state_or_states)
    seed_node_list = get_random_nodes_for_states(state_or_states)
    for seed_node in seed_node_list:
        jsonbody_js['ra.run-cli-configuration']['ra.target-list']['ra.target']['ra.node-ref'] = seed_node.get('node')
        jsonbody = json.dumps(jsonbody_js)
        uri = '/operations/v1/cisco-resource-activation:run-cli-configuration'
        jsonresponse = collectioncode.utils.rest_post_json(baseURL, uri, jsonbody, epnmuser, epnmpassword)
        try:
            thejson = json.loads(jsonresponse)
        except Exception as err:
            logging.critical('EPNM server is not configured with "show mpls topology" CLI template.  Halting execution.')
            sys.exit()

        jobname = thejson.get('ra.config-response').get('ra.job-status').get('ra.job-name')

        logging.info('Successfully submitted the API call to retrieve the MPLS topology.')
        logging.info('jobname is: ' + jobname)

        notDone = True
        logging.info('Checking job status...')
        results = ""
        while notDone:
            time.sleep(5)
            uri = "/operations/v1/cisco-resource-activation:get-cli-configuration-run-status/" + jobname
            jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
            thejson = json.loads(jsonresponse)
            try:
                status = thejson.get('ra.config-response').get('ra.job-status').get('ra.status')
                logging.info("Job status: " + str(status))
                if status == "SUCCESS":
                    logging.info("Successfully collected MPLS topology...")
                    results = thejson.get('ra.config-response').get('ra.deploy-result-list').get('ra.deploy-result').get('ra.transcript')
                    notDone = False
                elif status == "FAILURE":
                    logging.critical("Could not get MPLS topology!!!!!!")
                    sys.exit("Collection error.  Ending execution.")
            except KeyError:
                status = thejson.get('ra.config-response').get('ra.job-status').get('ra.run-status')
                logging.info("Run status: " + str(status))
                if status == "COMPLETED":
                    logging.info("Successfully collected MPLS topology...")
                    results = thejson['ra.deploy-result']['ra.transcript']
                    notDone = False
                elif status == "FAILURE":
                    logging.critical("Could not get MPLS topology!!!!!!")
                    sys.exit("Collection error.  Ending execution.")

        logging.info("Database received.")
        with open("jsongets/{state}_mplstopo.txt".format(state=seed_node.get('group')[-1].split('=')[-1].strip().replace(' ', '_')), 'wb') as f:
            f.write(results)
            f.close()


def collect_hostnames_json(baseURL, epnmuser, epnmpassword, state_or_states):
    with open("collectioncode/post-cli-template-hostname.json", 'r') as f:
        jsonbody = f.read()

    jsonbody_js = json.loads(jsonbody)
    ## Get Seed Nodes Based on State or States (New York, Flordia)
    run_get_4k_seed_nodes()
    get_potential_seednode(state_or_states)
    seed_node_list = get_random_nodes_for_states(state_or_states)
    for seed_node in seed_node_list:
        jsonbody_js['ra.run-cli-configuration']['ra.target-list']['ra.target']['ra.node-ref'] = seed_node.get('node')
        jsonbody = json.dumps(jsonbody_js)

        uri = '/operations/v1/cisco-resource-activation:run-cli-configuration'
        jsonresponse = collectioncode.utils.rest_post_json(baseURL, uri, jsonbody, epnmuser, epnmpassword)

        try:
            thejson = json.loads(jsonresponse)
        except Exception as err:
            logging.critical('EPNM server is not configured with "show isis hostname" CLI template.  Halting execution.')
            sys.exit()

        jobname = thejson.get('ra.config-response').get('ra.job-status').get('ra.job-name')

        logging.info('Successfully submitted the API call to retrieve the ISIS hostnames.')
        logging.info('jobname is: ' + jobname)

        notDone = True
        logging.info('Checking job status...')
        results = ""
        while notDone:
            time.sleep(5)
            uri = "/operations/v1/cisco-resource-activation:get-cli-configuration-run-status/" + jobname
            jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
            thejson = json.loads(jsonresponse)
            try:
                status = thejson.get('ra.config-response').get('ra.job-status').get('ra.status')
                logging.info("Job status: " + str(status))
                if status == "SUCCESS":
                    logging.info("Successfully collected ISIS hostnames...")
                    results = thejson.get('ra.config-response').get('ra.deploy-result-list').get('ra.deploy-result').get('ra.transcript')
                    notDone = False
                elif status == "FAILURE":
                    logging.critical("Could not get MPLS topology!!!!!!")
                    sys.exit("Collection error.  Ending execution.")
            except KeyError:
                status = thejson.get('ra.config-response').get('ra.job-status').get('ra.run-status')
                logging.info("Run status: " + status)
                if status == "COMPLETED":
                    logging.info("Successfully collected ISIS hostnames...")
                    results = thejson.get('ra.deploy-result').get('ra.transcript')
                    notDone = False
                elif status == "FAILURE":
                    logging.critical("Could not get ISIS hostnames!!!!!!")
                    sys.exit("Collection error.  Ending execution.")

        logging.info("Database received.")
        with open("jsongets/{state}_hostnames.txt".format(state=seed_node.get('group')[-1].split('=')[-1].strip().replace(' ', '_')), 'wb') as f:
            f.write(results)
            f.close()


def process_hostnames(state_or_states):
    for state in state_or_states:
        nodes = []
        with open("jsongets/{state}_hostnames.txt".format(state=state.strip().replace(' ', '_')), 'rb') as f:
            lines = f.read().splitlines()
            ilines = lines
            c = 0
            start = False
            for line in ilines:
                if "Level  System ID      Dynamic Hostname" in line:
                    start = True
                    continue
                elif start == True:
                    line_list = line.split(" ")
                    if len(line_list) > 3:
                        isis_id = line_list[-2]
                        hostname = line_list[-1]
                        nodes.append({'isis_id': isis_id, 'hostname': hostname})
                    else:
                        break
                c += 1

        with open("jsonfiles/{state}_hostnames.json".format(state=state.strip().replace(' ', '_')), "wb") as f:
            f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))


def processMPLS(state_or_states):
    for state in state_or_states:
        nodes = {}
        with open("jsongets/{state}_mplstopo.txt".format(state=state.strip().replace(' ', '_')), 'rb') as f:
            lines = f.read().splitlines()
            ilines = lines
            c = 0
            otn_flag = False
            for line in ilines:
                if "IGP Id: " in line:
                    if "OSPF OTN" in line:
                        otn_flag = True
                        continue
                    else:
                        otn_flag = False
                    isis_id = line.split(',')[0].split(':')[1].split(' ')[1].rsplit('.', 1)[0]
                    node = hostname_lookup(isis_id, state)
                    logging.info("processing node: " + node + " ISIS ID: " + isis_id + " line: " + str(c))
                    # if isis_id == "0010.0040.1069":
                    #     print "found it!"
                    loopback = line.split(',')[1].split(':')[1].split(' ')[1]
                    nodes[node] = {'Loopback Address': loopback}
                    nodes[node]['Links'] = dict()
                    i = 0
                    foundfirstlink = False
                elif "Link[" in line and "Nbr IGP Id" in line and not otn_flag:
                    try:
                        neighbor_isis_id = line.split(',')[1].split(':')[1].rsplit('.', 1)[0]
                        neighbor_node_id = line.split(',')[2].split(':')[1]
                        neighbor = hostname_lookup(neighbor_isis_id, state)
                        if neighbor_node_id == "-1":
                            continue
                        if neighbor == None:
                            logging.warn("There was a problem parsing the neighbor!")
                            logging.critical("Critical error!")
                            sys.exit("MPLS topology is not complete for node " + node + "!!! Halting execution!")
                        i += 1
                        linkid = "Link" + str(i)
                        nodes[node]['Links'][linkid] = dict([('Neighbor', neighbor)])
                    except Exception as err:
                        logging.warn("There was a problem parsing the neighbor!")
                        logging.exception(err)
                        logging.critical("Critical error!")
                        sys.exit("ISIS database is not complete for node " + node + "!!! Halting execution!")
                    foundfirstlink = True
                elif "TE Metric:" in line and foundfirstlink and not otn_flag:
                    try:
                        te_metric = line.split(',')[0].split(':')[1]
                        nodes[node]['Links'][linkid]['TE Metric'] = te_metric
                        igp_metric = line.split(',')[1].split(':')[1]
                        nodes[node]['Links'][linkid]['IGP Metric'] = igp_metric
                    except Exception as err:
                        logging.warn("There was a problem parsing the metric!")
                        logging.exception(err)
                        logging.critical("Critical error!")
                        sys.exit("ISIS database is not complete for node " + node + "!!! Halting execution!")
                elif "Attribute Flags:" in line and foundfirstlink and not otn_flag:
                    affinity = line.split(':')[1].strip()
                    nodes[node]['Links'][linkid]['Affinity'] = affinity
                elif "Intf Address:" in line and not 'Nbr' in line and foundfirstlink and not otn_flag:
                    localIP = line.split(',')[1].split(':')[1]
                    nodes[node]['Links'][linkid]['Local IP'] = localIP
                elif "Nbr Intf Address:" in line and foundfirstlink == True and not otn_flag:
                    neighIP = line.split(',')[0].split(':')[1]
                    nodes[node]['Links'][linkid]['Neighbor IP'] = neighIP
                elif "Max Reservable BW Global:" in line and foundfirstlink and not otn_flag:
                    rsvpBW = line.split(',')[1].split(':')[1].split(' ')[0]
                    phyBW = line.split(',')[0].split(':')[1].split(' ')[0]
                    nodes[node]['Links'][linkid]['RSVP BW'] = rsvpBW
                    nodes[node]['Links'][linkid]['Phy BW'] = phyBW
                elif "SRLGs:" in line and foundfirstlink and not otn_flag:
                    nodes[node]['Links'][linkid]['SRLGs'] = dict()
                    d = 0
                    srlgs = []
                    while True:
                        tline = ilines[c + d]
                        if not ("Switching Capability:" in tline):
                            if ':' in tline:
                                srlgs = srlgs + tline.strip().split(':')[1].split(',')
                            else:
                                srlgs = srlgs + tline.strip().split(',')
                            d += 1
                        else:
                            break
                    cleaned_srlgs = []
                    for srlg in srlgs:
                        cleaned_srlgs.append(''.join(srlg.split()))
                    nodes[node]['Links'][linkid]['SRLGs'] = cleaned_srlgs
                c += 1

            with open("jsonfiles/{state}_l3Links.json".format(state=state.strip().replace(' ', '_')), "wb") as f:
                f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))



def hostname_lookup(isis_id, state):
    with open("jsonfiles/{state}_hostnames.json".format(state=state.strip().replace(' ', '_')), 'rb') as f:
        jsonresponse = f.read()

    hostnames = json.loads(jsonresponse)
    #print (hostnames)
    for host in hostnames:
        if host.get('isis_id') == isis_id:
            return host.get('hostname')
    return None


def collectMPLSnodes():
    with open("jsongets/tl-mpls-link-layer.json", 'rb') as f:
        thejson = json.load(f)

    mpls_links = thejson.get('com.response-message').get('com.data').get('topo.topological-link')
    mpls_nodes = []
    for mpls_link in mpls_links:
        try:
            tmp_ep_list = mpls_link.get('topo.endpoint-list').get('topo.endpoint')
            if len(tmp_ep_list) == 2:
                for ep in tmp_ep_list:
                    tmp_node = ep['topo.endpoint-ref'].split('!')[1].split('=')[1]
                    if tmp_node not in mpls_nodes:  mpls_nodes.append(tmp_node)
        except Exception as err:
            logging.warn("Invalid or missing end-point list for " + mpls_link['topo.fdn'])

    with open("jsonfiles/mpls_nodes.json", "wb") as f:
        f.write(json.dumps(mpls_nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))


def add_mpls_tl_data(baseURL, epnmuser, epnmpassword, state_or_states):
    for state in state_or_states:
        with open("jsongets/tl-mpls-link-layer.json", 'rb') as f:
            jsonresponse = f.read()

        thejson = json.loads(jsonresponse)

        with open("jsonfiles/{state}_l3Links.json".format(state=state.strip().replace(' ', '_')), 'rb') as f:
            l3links = json.load(f)

        names = []
        for k1, v1 in l3links.items():
            logging.info("Nodename is: " + k1)
            for k2, v2 in v1.items():
                if isinstance(v2, dict):
                    for k3, v3 in v2.items():
                        logging.info("Linkname is: " + k3)
                        n1IP = v3.get('Local IP')
                        n2IP = v3.get('Neighbor IP')
                        name1 = n1IP + '-' + n2IP
                        name2 = n2IP + '-' + n1IP
                        matchedlink = False
                        for item in thejson.get('com.response-message').get('com.data').get('topo.topological-link'):
                            fdn = item.get('topo.fdn')
                            discoveredname = item.get('topo.discovered-name')
                            if (name1 == discoveredname or name2 == discoveredname):
                                logging.info("Matched link in EPNM MPLS TL with discovered-name: " + discoveredname)
                                matchedlink = True
                                v3['discoveredname'] = discoveredname
                                # try:
                                #     if isinstance(item['topo.endpoint-list']['topo.endpoint'], list):
                                #         logging.info("End point list is valid...")
                                #     else:
                                #         logging.info(("!!!End point list is not valid!!!"))
                                # except Exception as err:
                                #     logging.critical("Missing endpoint-ref for " + k1 + " " + k3 + " " + discoveredname)
                                #     logging.warn("Removing link from topology...")
                                #     v2.pop(k3)
                                try:
                                    parse1 = item.get('topo.endpoint-list').get('topo.endpoint')[0].get('topo.endpoint-ref')
                                    node1 = parse1.split('!')[1].split('=')[1]
                                    node1intf = parse1.split('!')[2].split('=')[2]
                                    node1intfparsed = node1intf.split('-')[0]

                                    parse2 = item.get('topo.endpoint-list').get('topo.endpoint')[1].get('topo.endpoint-ref')
                                    node2 = parse2.split('!')[1].split('=')[1]
                                    node2intf = parse2.split('!')[2].split('=')[2]
                                    node2intfparsed = node2intf.split('-')[0]

                                    if node2 == v3.get('Neighbor'):
                                        v3['Neighbor Intf'] = node2intfparsed
                                        v3['Local Intf'] = node1intfparsed
                                        v3['Link Speed'], v3['lr type'], v3['Bandwidth'] = parseintftype(node1intfparsed)
                                    elif node1 == v3['Neighbor']:
                                        v3['Neighbor Intf'] = node1intfparsed
                                        v3['Local Intf'] = node2intfparsed
                                        v3['Link Speed'], v3['lr type'], v3['Bandwidth'] = parseintftype(node2intfparsed)
                                    else:
                                        logging.warn(
                                            "Could not match node names for interface assignment for node " + k1 + " link " + k3)
                                        logging.warn("Removing link from topology...")
                                        v2.pop(k3)
                                    break
                                except Exception as err:
                                    logging.critical("Missing endpoint-ref for " + k1 + " " + k3 + " " + discoveredname)
                                    logging.warn("Removing link from topology...")
                                    v2.pop(k3)
                        if not matchedlink:
                            logging.warn(
                                "Could not match discovered name for node " + k1 + " link " + k3 + ": " + name1 + " or " + name2)
                            logging.warn("Removing link from topology...")
                            v2.pop(k3)
        with open("jsonfiles/{state}_l3Links_add_tl.json".format(state=state.strip().replace(' ', '_')), "wb") as f:
            f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))

        

def collect_mpls_links_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=mpls-link-layer&.startIndex=" + str(
            startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/tl-mpls-link-layer.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))


def collect_otu_links_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=otu-link-layer&.startIndex=" + str(
            startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/tl-otu-link-layer.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))

    with open("jsongets/tl-otu-link-layer.json", 'rb') as f:
        jsonresponse = f.read()

    thejson = json.loads(jsonresponse)

    otu_links = []
    for item in thejson.get('com.response-message').get('com.data').get('topo.topological-link'):
        try:
            otu_link = {}
            termination_points = []
            fdn = item.get('topo.fdn')
            logging.info("Collecting OTU link " + fdn)
            discoveredname = item.get('topo.discovered-name')
            capacity = item.get('topo.total-capacity')
            ep_list = item.get('topo.endpoint-list').get('topo.endpoint')
            endpoints = []
            for ep in ep_list:
                tmptp = {}
                tmptp.setdefault('node', ep.get('topo.endpoint-ref').split('!')[1].split('=')[1])
                tmptp.setdefault('port', ep.get('topo.endpoint-ref').split('!')[2].split('=')[2].split(';')[0])
                tmptp.setdefault('tp-fdn', ep.get('topo.endpoint-ref') + "&containedCTP=true")
                try:
                    tmptp['port-num'] = tmptp.get('port').split('OTUC2')[1]
                except Exception as err:
                    tmptp['port-num'] = tmptp.get('port').split('OTU4')[1]
                termination_points.append(tmptp)
            otu_link.setdefault('fdn', fdn)
            otu_link.setdefault('discoveredname', discoveredname)
            otu_link.setdefault('capacity', capacity)
            otu_link.setdefault('termination-points', termination_points)
            if len(ep_list) == 2:
                otu_links.append(otu_link)
            else:
                logging.warn("Endpoint list for " + fdn + " is incomplete!")
        except Exception as error:
            logging.warn("Invalid OTU topo link!")

    with open("jsonfiles/otu_links.json", "wb") as f:
        f.write(json.dumps(otu_links, f, sort_keys=True, indent=4, separators=(',', ': ')))


def collect_otu_termination_points_threaded(baseURL, epnmuser, epnmpassword):
    with open("jsonfiles/otu_links.json", 'rb') as f:
        otu_links = json.load(f)

    tpfdns = []
    for otu_link in otu_links:
        for tp in otu_link.get('termination-points'):
            tpfdn = tp.get('tp-fdn')
            tpfdn_dict = {'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword, 'tpfdn': tpfdn}
            tpfdns.append(tpfdn_dict)

    logging.info("Spawning threads to collect termination points...")
    pool = ThreadPool(wae_api.thread_count)
    termination_points = pool.map(process_otu_tpfdn, tpfdns)
    pool.close()
    pool.join()

    for otu_link in otu_links:
        if otu_link.get('termination-points'):
            for tp in otu_link.get('termination-points'):
                channels = []
                for tmptp in termination_points:
                    try:
                        for channel in tmptp:
                            if channel.get('tp-fdn') and tp.get('tp-fdn'):
                                if channel.get('tp-fdn') == tp.get('tp-fdn'):
                                    tmpchannel = channel.copy()
                                    tmpchannel.pop('tp-fdn', None)
                                    channels.append(tmpchannel)
                    except Exception as err:
                        logging.warn("TP for OTU link is invalid.")
                tp.setdefault('channels', channels)

    with open("jsonfiles/otu_links.json", "wb") as f:
        f.write(json.dumps(otu_links, f, sort_keys=True, indent=4, separators=(',', ': ')))


def process_otu_tpfdn(tpfdn_dict):
    tp_info = collect_otu_termination_point(tpfdn_dict['baseURL'], tpfdn_dict['epnmuser'], tpfdn_dict['epnmpassword'],
                                            tpfdn_dict['tpfdn'])
    return tp_info


def collect_otu_termination_point(baseURL, epnmuser, epnmpassword, tpfdn):
    try:
        logging.info("Making API call to collect OTU termination point for tpFdn " + tpfdn)
        uri = "/data/v1/cisco-resource-ems:termination-point?fdn=" + tpfdn
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)

        filename = "jsongets/tp-data-" + tpfdn.split('!')[1] + tpfdn.split('!')[2].split(';')[0].replace('/',
                                                                                                         '-') + ".json"
        logging.info("Filename is " + filename)
        with open(filename, 'wb') as f:
            f.write(jsonresponse)

        with open(filename, 'rb') as f:
            jsonresponse = json.load(f)

        logging.info("Parsing termination_point results for vcFdn " + tpfdn)
        termination_points = jsonresponse.get('com.response-message').get('com.data').get('tp.termination-point')
        tp_data = []
        if isinstance(termination_points, list):
            is_first_tp = True
            for tp in termination_points:
                if tp.get('tp.layer-rate') == "oc:lr-och-data-unit-c2" or tp.get('tp.layer-rate') == "oc:lr-och-data-unit-2":
                    logging.info("vcFDN " + tpfdn + " tp.layer-rate is oc:lr-och-data-unit-c2...skipping this tp")
                    continue
                tp_dict = {}
                tp_dict.setdefault('ch-fdn', tp.get('tp.fdn'))
                tp_dict.setdefault('tp-fdn', tpfdn)
                tp_dict.setdefault('layer-rate', tp.get('tp.layer-rate'))
                tp_dict.setdefault('bandwidth', tp.get('tp.if-speed'))
                tp_dict.setdefault('channel', tp.get('tp.fdn').split('!')[2].split(';')[0].split('=')[2])
                try:
                    logging.info("OTU TP termination-mode is Ethernet " + tp.get('tp.fdn'))
                    tp_dict['termination-mode'] = tp['tp.optical-attributes']['tp.termination-mode']
                    tp_data.append(tp_dict)
                except Exception as error:
                    logging.info("OTU TP termination-mode is OTN " + tp['tp.fdn'])
                    tp_dict['termination-mode'] = "OTN"
                    tp_data.append(tp_dict)
        else:
            tp_dict = {}
            tp_dict.setdefault('ch-fdn', termination_points.get('tp.fdn'))
            tp_dict.setdefault('tp-fdn', tpfdn)
            tp_dict.setdefault('layer-rate', termination_points.get('tp.layer-rate'))
            tp_dict.setdefault('bandwidth', termination_points.get('tp.if-speed'))
            tp_dict.setdefault('channel', termination_points.get('tp.fdn').split('!')[2].split(';')[0].split('=')[2])
            try:
                tp_dict['termination-mode'] = termination_points['tp.optical-attributes']['tp.termination-mode']
                tp_data.append(tp_dict)
            except Exception as error:
                logging.info("OTU TP termination-mode is OTN " + termination_points['tp.fdn'])
                tp_dict['termination-mode'] = "OTN"
                tp_data.append(tp_dict)
        return tp_data
    except Exception as err:
        logging.warn("OTU termination point collection failed for tpfdn " + tpfdn)
        
        
def collectvirtualconnections_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-service-network:virtual-connection?type=optical&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition.get('com.response-message').get('com.header').get('com.firstIndex')
        lastindex = jsonaddition.get('com.response-message').get('com.header').get('com.lastIndex')
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/vc-optical.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))


def add_vcfdn_l3links(state_or_states):
    for state in state_or_states:
        with open("jsonfiles/{state}_l3Links_final.json".format(state=state.strip().replace(' ', '_')), 'rb') as f:
            l3links = json.load(f)

        with open("jsongets/vc-optical.json", 'rb') as f:
            jsonresponse = f.read()

        thejson = json.loads(jsonresponse)

        for item in thejson.get('com.response-message').get('com.data').get('vc.virtual-connection'):
            matched_fdn = False
            fdn = item.get('vc.fdn')
            subtype = item.get('vc.subtype')
            if subtype == "oc:och-trail-uni":
                vcdict = {}
                try:
                    for subitem in item.get('vc.termination-point-list').get('vc.termination-point'):
                        tmpfdn = subitem.get('vc.fdn')
                        tmpnode = tmpfdn.split('!')[1].split('=')[1]
                        tmpoptics = tmpfdn.split('!')[2].split('=')[2].split(';')[0]
                        vcdict.setdefault(tmpnode, tmpoptics)
                    for k1, v1 in l3links.items():
                        # logging.info "**************Nodename is: " + k1
                        for k2, v2 in v1.items():
                            if isinstance(v2, dict):
                                for k3, v3 in v2.items():
                                    # logging.info "***************Linkname is: " + k3
                                    for node, intf in vcdict.items():
                                        if node == k1:
                                            if parseintfnum(intf) == parseintfnum(v3.get('Local Intf')):
                                                v3.setdefault('vc-fdn', fdn)
                                                matched_fdn = True
                                                logging.info("Matched vc-fdn " + fdn + " for node " + k1 + " link " + k3)
                    if not matched_fdn:
                        pass
                except KeyError:
                    logging.error("Could not get virtual connection for " + fdn)
                except TypeError:
                    logging.error("Missing or invalid end-point list for  " + fdn)
        logging.info("Completed collecting virtual connections...")
        with open("jsonfiles/{state}_l3Links_final.json".format(state=state.strip().replace(' ', '_')), "wb") as f:
            f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))


def parse_otn_links():
    with open("jsonfiles/otu_links.json", 'rb') as f:
        otu_links = json.load(f)

    otn_links = []
    for otu_link in otu_links:
        mpls_channels = []
        otn_channels = []
        if otu_link.get('termination-points'):
            for tp in otu_link['termination-points']:
                if tp.get('channels'):
                    for channel in tp.get('channels'):
                        tmp_channel = {}
                        tmp_channel.setdefault('channel', channel.get('channel'))
                        tmp_channel.setdefault('node', tp.get('node'))
                        if channel.get('termination-mode') == 'OTN':
                            otn_channels.append(tmp_channel)
                        elif channel.get('termination-mode') == 'ETHERNET_PACKET':
                            mpls_channels.append(tmp_channel)

        for otn_channel in otn_channels:
            if len(otn_channel) == 0: continue
            for otn_channel_compare in otn_channels:
                if len(otn_channel_compare) == 0: continue
                try:
                    ch = otn_channel.get('channel').split('/')[4]
                    ch_compare = otn_channel_compare.get('channel').split('/')[4]
                except:
                    logging.warn("Channel derived from 100G non-channelized wavelength, setting channel to 1.")
                    ch = 1
                    ch_compare = 1
                if otn_channel.get('node') != otn_channel_compare.get('node') and ch == ch_compare:
                    otn_link = {}
                    otn_link_ep = {}
                    otn_link.setdefault('name', "OTN link " + otn_channel.get('node') + " to " + otn_channel_compare.get('node') + " " + otn_channel.get('channel'))
                    otn_link.setdefault('name', otu_link.get('fdn').split("=")[2] + " ODU4 channel " + ch)
                    try:
                        otn_link.setdefault('och-trail-fdn', otu_link.get('och-trail-fdn'))
                        otn_link.setdefault('otu-link-fdn', otu_link.get('fdn'))
                        otn_link_endpoints = []
                        otn_link_endpoints.append({'node': otn_channel.get('node'), 'channel': otn_channel.get('channel')})
                        otn_link_endpoints.append({'node': otn_channel_compare.get('node'), 'channel': otn_channel_compare.get('channel')})
                        otn_link.setdefault('endpoints', otn_link_endpoints)
                        otn_links.append(otn_link)
                        otn_channels.pop(0)
                        logging.info("Successfully parsed OTN link from OTU link " + otu_link.get('fdn'))
                    except Exception as err:
                        logging.warn("Could not parse OTN link from OTU link for " + otu_link.get('fdn'))

    with open("jsonfiles/otn_links.json", "wb") as f:
        f.write(json.dumps(otn_links, f, sort_keys=True, indent=4, separators=(',', ': ')))


def parse_vc_optical_och_trails():
    with open("jsongets/vc-optical.json", 'rb') as f:
        jsonresponse = f.read()

    thejson = json.loads(jsonresponse)
    och_trails = []
    for item in thejson.get('com.response-message').get('com.data').get('vc.virtual-connection'):
        vcdict = {}
        fdn = item.get('vc.fdn')
        subtype = item.get('vc.subtype')
        termination_points = []
        if subtype == "oc:och-trail-uni":
            vcdict.setdefault('fdn', fdn)
            vcdict.setdefault('subtype', subtype)
            vcdict.setdefault('termination-points', termination_points)
            try:
                vcdict.setdefault('trail-fdn', item.get('vc.carried-by-vc-ref-list').get('vc.carried-by-vc-ref'))
            except Exception as error:
                logging.warn("Could not determine trail-fdn for OCH-trail " + fdn)
            try:
                item_tps = item.get('vc.termination-point-list').get('vc.termination-point')
                if len(item_tps) == 2:
                    for subitem in item_tps:
                        tmptp = {}
                        tmpfdn = subitem.get('vc.fdn')
                        tmptp.setdefault('node', tmpfdn.split('!')[1].split('=')[1])
                        tmptp.setdefault('port', tmpfdn.split('!')[2].split('=')[2].split(';')[0])
                        tmptp.setdefault('port-num', tmptp['port'].split('Optics')[1])
                        termination_points.append(tmptp)
                    och_trails.append(vcdict)
                else:
                    logging.warn("OCH-trail " + fdn + " has incomplete termination points!")
            except KeyError:
                logging.error("Could not get virtual connection for " + fdn)
            except TypeError:
                logging.error("Missing or invalid end-point list for  " + fdn)

    logging.info("Completed parsing OCH Trails...")
    with open("jsonfiles/och_trails.json", "wb") as f:
        f.write(json.dumps(och_trails, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def add_wavelength_vc_optical_och_trails():
    with open("jsongets/vc-optical.json", 'rb') as f:
        jsonresponse = f.read()

    thejson = json.loads(jsonresponse)

    with open("jsonfiles/och_trails.json", 'rb') as f:
        jsonresponse = f.read()

    och_trails = json.loads(jsonresponse)
    virtual_connections = thejson.get('com.response-message').get('com.data').get('vc.virtual-connection')

    for och_trail in och_trails:
        for vc in virtual_connections:
            fdn = vc.get('vc.fdn')
            subtype = vc.get('vc.subtype')
            if subtype == "oc:och-nc":
                if fdn == och_trail.get('trail-fdn'):
                    och_trail.setdefault('wavelength', vc['vc.och-nc']['vc.wavelength'])

    logging.info("Completed getting OCH Trails wavelengths...")
    with open("jsonfiles/och_trails.json", "wb") as f:
        f.write(json.dumps(och_trails, f, sort_keys=True, indent=4, separators=(',', ': ')))


def parse_odu_services():
    with open("jsongets/vc-optical.json", 'rb') as f:
        thejson = json.load(f)

    virtual_connections = thejson.get('com.response-message').get('com.data').get('vc.virtual-connection')
    odu_services = []
    for vc in virtual_connections:
        if vc.get('vc.subtype') == "oc:och-odu-uni":
            try:
                odu_service = {}
                odu_service.setdefault('fdn', vc.get('vc.fdn'))
                odu_service.setdefault('discovered-name', vc.get('vc.discovered-name'))
                odu_service.setdefault('carrying-odu-tunnel', vc.get('vc.carrying-vc-ref-list').get('vc.carrying-vc-ref'))
                termination_points = vc.get('vc.termination-point-list').get('vc.termination-point')
                if len(termination_points) == 2:
                    odu_service.setdefault('node-A', termination_points[0]['vc.fdn'].split('!')[1].split('=')[1])
                    odu_service.setdefault('node-A-intf', termination_points[0]['vc.alias-name'])
                    odu_service.setdefault('node-B', termination_points[1]['vc.fdn'].split('!')[1].split('=')[1])
                    odu_service.setdefault('node-B-intf', termination_points[1].get('vc.alias-name'))
                for tmp_vc in virtual_connections:
                    if tmp_vc.get('vc.fdn') and odu_service.get('carrying-odu-tunnel'):
                        if tmp_vc.get('vc.fdn') == odu_service.get('carrying-odu-tunnel'):
                            odu_service.setdefault('bandwidth', tmp_vc.get('vc.odu-tunnel').get('vc.bandwidth'))
                            break
                odu_services.append(odu_service)
            except Exception as err:
                logging.warn("Problem processing ODU service, skipping...")
                continue

    with open("jsonfiles/odu_services.json", "wb") as f:
        f.write(json.dumps(odu_services, f, sort_keys=True, indent=4, separators=(',', ': ')))


def collect_multilayer_route_odu_services_threaded(baseURL, epnmuser, epnmpassword):
    with open("jsonfiles/odu_services.json", 'rb') as f:
        odu_services = json.load(f)

    vcfdns = []
    for odu_service in odu_services:
        vcfdn = odu_service.get('fdn')
        vcfdn_dict = {'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword, 'vcfdn': vcfdn}
        vcfdns.append(vcfdn_dict)
    logging.info("Spawning threads to collect multi-layer routes for OCH-trails...")
    pool = ThreadPool(wae_api.thread_count)
    otu_links = pool.map(process_vcfdn_odu_service, vcfdns)
    pool.close()
    pool.join()

    logging.info("Completed collecting multi-layer routes...")
    logging.info("Processing multi-layer routes...")
    for odu_service in odu_services:
        tmp_vcfdn = odu_service.get('fdn')
        if len(otu_links) > 0:
            for result in otu_links:
                if result:
                    if 'otu-links' in result:
                        if result.get('vcfdn') == tmp_vcfdn:
                            logging.info("Multi-layer route collection successful for vcFdn " + tmp_vcfdn)
                            odu_service.setdefault('otu-links', result.get('otu-links'))


    logging.info("Completed collecting OTU links for ODU services...")
    with open("jsonfiles/odu_services.json", "wb") as f:
        f.write(json.dumps(odu_services, f, sort_keys=True, indent=4, separators=(',', ': ')))


def add_och_trails_to_otu_links():
    with open("jsonfiles/otu_links.json", 'rb') as f:
        otu_links = json.load(f)

    with open("jsonfiles/och_trails.json", 'rb') as f:
        och_trails = json.load(f)

    for otu_link in otu_links:
        otu_ports = []
        matched = False
        if otu_link.get('termination-points'):
            for otu_tp in otu_link.get('termination-points'):
                tp_dict = {'node': otu_tp.get('node'), 'port-num': otu_tp.get('port-num')}
                otu_ports.append(tp_dict)
                for och_trail in och_trails:
                    och_ports = []
                    if och_trail.get('termination-points'):
                        for och_trail_tp in och_trail.get('termination-points'):
                            tmp_tp = {'node': och_trail_tp.get('node'), 'port-num': och_trail_tp.get('port-num')}
                            och_ports.append(tmp_tp)
                        for tp in och_ports:
                            if tp not in otu_ports:
                                matched = False
                            elif tp in otu_ports:
                                matched = True
                        if matched:
                            otu_link.setdefault('och-trail-fdn', och_trail.get('fdn'))
                            break
        if not matched:
            logging.warn("Could not find och-trail-fdn for otu_link " + otu_link.get('fdn'))

    logging.info("Completed adding OCH trails to OTU links...")
    with open("jsonfiles/otu_links.json", "wb") as f:
        f.write(json.dumps(otu_links, f, sort_keys=True, indent=4, separators=(',', ': ')))



def addL1hopstoOCHtrails_threaded(baseURL, epnmuser, epnmpassword):
    with open("jsonfiles/och_trails.json", 'rb') as f:
        och_trails = json.load(f)

    vcfdns = []
    for och_trail in och_trails:
        if 'fdn' in och_trail:
            vcfdn = och_trail['fdn']
            vcfdn_dict = {'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword,
                          'vcfdn': vcfdn}
            if not vcfdn_dict in vcfdns:
                vcfdns.append(vcfdn_dict)
    logging.info("Spawning threads to collect multi-layer routes for OCH-trails...")
    pool = ThreadPool(wae_api.thread_count)
    l1hops = pool.map(process_vcfdn, vcfdns)
    pool.close()
    pool.join()

    logging.info("Completed collecting multi-layer routes...")
    logging.info("Processing multi-layer routes...")
    for och_trail in och_trails:
        if 'fdn' in och_trail:
            tmp_vcfdn = och_trail.get('fdn')
            if len(l1hops) > 0:
                for l1hopset in l1hops:
                    if len(l1hopset) > 1:
                        if l1hopset['vcfdn'] == tmp_vcfdn:
                            logging.info(
                                "Multi-layer route collection successful for vcFdn " + tmp_vcfdn)
                            och_trail['L1 Hops'] = l1hopset.copy()
                            och_trail['L1 Hops'].pop('vcfdn')

    logging.info("Completed collecting L1 paths for OCH-trails...")
    with open("jsonfiles/och_trails.json", "wb") as f:
        f.write(json.dumps(och_trails, f, sort_keys=True, indent=4, separators=(',', ': ')))


def process_vcfdn(vcfdn_dict):
    l1hops = collectmultilayerroute_json(vcfdn_dict['baseURL'], vcfdn_dict['epnmuser'], vcfdn_dict['epnmpassword'],
                                         vcfdn_dict['vcfdn'])
    return l1hops


def collectmultilayerroute_json(baseURL, epnmuser, epnmpassword, vcfdn):
    l1hops = {}
    logging.info("Making API call to collect multi_layer route for vcFdn " + vcfdn)
    uri = "/data/v1/cisco-resource-network:virtual-connection-multi-layer-route?vcFdn=" + vcfdn
    try:
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
    except Exception as err:
        logging.warn("API call failed to retrieve multilayer route for vcFDN " + vcfdn)
        logging.warn("Check this vcFdn and debug with EPNM team if necessary.")
        return l1hops

    try:
        with open("jsongets/multilayer_route_" + vcfdn + ".json", 'wb') as f:
            f.write(jsonresponse)
            f.close()

        with open("jsongets/multilayer_route_" + vcfdn + ".json", 'rb') as f:
            jsonresponse = f.read()
            f.close()
    except Exception as err:
        logging.warn("Could not save or open file for multilayer route for vcFDN " + vcfdn)
        logging.warn("Check this vcFdn and debug with EPNM team if necessary.")
        return l1hops

    logging.info("Parsing multilayer_route results for vcFdn " + vcfdn)
    try:
        thejson = json.loads(jsonresponse)

        l1hopsops = parsemultilayerroute_json(thejson, "topo:ops-link-layer", "Optics")
        l1hopsots = parsemultilayerroute_json(thejson, "topo:ots-link-layer", "LINE")
        if len(l1hopsops) == 0 or len(
                l1hopsots) == 0:  # check if either multilayer route parsing fails and exit the function if so
            logging.warn("Could not get multilayer route for vcFDN " + vcfdn)
            logging.warn("Check this vcFdn and debug with EPNM team if necessary.")
            return l1hops
        i = 1
        for k, v in l1hopsops.items():
            l1hops['L1 Hop' + str(i)] = v
            i += 1
        for k, v in l1hopsots.items():
            l1hops['L1 Hop' + str(i)] = v
            i += 1
        l1hops['vcfdn'] = vcfdn
        return l1hops
    except Exception as err:
        logging.warn("Could not save or open file for multilayer route for vcFDN " + vcfdn)
        logging.warn("Check this vcFdn and debug with EPNM team if necessary.")
        return l1hops


def parsemultilayerroute_json(jsonresponse, topologylayer, intftype):
    l1hops = {}
    tmpl1hops = {}
    tmpl1hops['Nodes'] = dict()
    firsthop = False
    i = 1
    if jsonresponse['com.response-message']['com.data']:
        if jsonresponse['com.response-message']['com.data']['topo.virtual-connection-multi-layer-route-list'].has_key('topo.virtual-connection-multi-layer-route'):
            for item in jsonresponse['com.response-message']['com.data']['topo.virtual-connection-multi-layer-route-list'][
                'topo.virtual-connection-multi-layer-route']:
                subtype = item['topo.topology-layer']
                if subtype == topologylayer:
                    try:
                        topo_links = item['topo.tl-list']['topo.topological-link']
                    except Exception as err:
                        logging.warning("Could not process multi-layer route response, skipping this fdn...")
                        break
                    if isinstance(topo_links, list):
                        for subitem in topo_links:
                            tmpfdn = subitem['topo.fdn']
                            try:
                                endpointlist = subitem['topo.endpoint-list']['topo.endpoint']
                            except Exception as err:
                                logging.error(
                                    "No endpoint-list or valid endpoints found in the " + topologylayer + " for this vcFdn!")
                                l1hops = {}
                                return l1hops
                            for subsubitem in subitem['topo.endpoint-list']['topo.endpoint']:
                                tmpep = subsubitem['topo.endpoint-ref']
                                tmpnode = tmpep.split('!')[1].split('=')[1]
                                tmpport = tmpep.split('!')[2].split('=')[2].split(';')[0]
                                tmpl1hops['Nodes'][tmpnode] = dict([('Port', tmpport)])
                            for key, val in tmpl1hops.get('Nodes').items():
                                porttype = val.get('Port')
                                if intftype in porttype: firsthop = True
                            if firsthop:
                                l1hops['L1 Hop' + str(i)] = tmpl1hops
                                l1hops['L1 Hop' + str(i)]['fdn'] = tmpfdn
                                i += 1
                            tmpl1hops = {}
                            tmpl1hops['Nodes'] = dict()
                            firsthop = False
                        i = 1
                    else:
                        tmpfdn = topo_links['topo.fdn']
                        try:
                            endpointlist = topo_links['topo.endpoint-list']['topo.endpoint']
                        except Exception as err:
                            logging.error(
                                "No endpoint-list or valid endpoints found in the " + topologylayer + " for this vcFdn!")
                            l1hops = {}
                            return l1hops
                        for subitem in topo_links['topo.endpoint-list']['topo.endpoint']:
                            tmpep = subitem['topo.endpoint-ref']
                            tmpnode = tmpep.split('!')[1].split('=')[1]
                            tmpport = tmpep.split('!')[2].split('=')[2].split(';')[0]
                            tmpl1hops['Nodes'][tmpnode] = dict([('Port', tmpport)])
                        for key, val in tmpl1hops.get('Nodes').items():
                            porttype = val.get('Port')
                            if intftype in porttype: firsthop = True
                        if firsthop:
                            l1hops['L1 Hop' + str(i)] = tmpl1hops
                            l1hops['L1 Hop' + str(i)]['fdn'] = tmpfdn
                            i += 1
                        tmpl1hops = {}
                        tmpl1hops['Nodes'] = dict()
                        firsthop = False
                        i = 1
    return l1hops


def reorderl1hops_och_trails():
    with open("jsonfiles/och_trails.json", 'rb') as f:
        och_trails = json.load(f)
        f.close()

    for och_trail in och_trails:
        if 'L1 Hops' in och_trail:
            logging.info("OCH-trail " + och_trail['fdn'] + " has L1 hops.  Processing...")
            l1hops = []
            vcfdn = och_trail['fdn']
            for k4, v4 in och_trail['L1 Hops'].items():
                nodelist = []
                for k5, v5 in v4.get('Nodes').items():
                    nodelist.append(k5)
                l1hops.append(nodelist)
            # if k1 == "LYBRNYLB-01153A08A" and k3 == "Link9":
            #     pass
            ref_node = och_trail['termination-points'][0]['node']
            l1hopsordered = returnorderedlist(ref_node, l1hops)
            if l1hopsordered == None:
                logging.warn("Error generating ordered L1 hops for vcFdn=" + vcfdn)
                logging.warn(
                    "Removing L1 hops from this link.  Check this vcFdn and debug with EPNM team if necessary.")
                och_trail.pop('L1 Hops')
                break
            tmphops = []
            completed = False
            while not completed:
                if len(l1hopsordered) == 0: completed = True
                for hop in l1hopsordered:
                    for k4, v4 in och_trail.get('L1 Hops').items():
                        tmpnodes = []
                        for k5, v5 in v4.get('Nodes').items():
                            tmpnodes.append(k5)
                        if (hop[0] == tmpnodes[0] and hop[1] == tmpnodes[1]) or \
                                (hop[0] == tmpnodes[1] and hop[1] == tmpnodes[0]):
                            tmphops.append(v4)
                            l1hopsordered.remove(hop)
                            break
                    break
            och_trail['Ordered L1 Hops'] = tmphops
            och_trail.pop('L1 Hops')
            # logging.info "next L1 hop..."
    with open("jsonfiles/och_trails.json", "wb") as f:
        f.write(json.dumps(och_trails, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def reorderl1hops():
    ##### unused function #######
    with open("jsonfiles/l3Links_add_l1hops.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    for k1, v1 in l3links.items():
        # logging.info "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.info "***************Linkname is: " + k3
                    if 'L1 Hops' in v3:
                        logging.info("Node " + k1 + " " + k3 + " has L1 hops.  Processing...")
                        l1hops = []
                        vcfdn = v3['vc-fdn']
                        for k4, v4 in v3.get('L1 Hops').items():
                            nodelist = []
                            for k5, v5 in v4.get('Nodes').items():
                                nodelist.append(k5)
                            l1hops.append(nodelist)
                        if k1 == "LYBRNYLB-01153A08A" and k3 == "Link9":
                            pass
                        l1hopsordered = returnorderedlist(k1, l1hops)
                        if l1hopsordered == None:
                            logging.warn("Error generating ordered L1 hops for vcFdn=" + vcfdn)
                            logging.warn(
                                "Removing L1 hops from this link.  Check this vcFdn and debug with EPNM team if necessary.")
                            v3.pop('L1 Hops')
                            break
                        tmphops = []
                        completed = False
                        while not completed:
                            if len(l1hopsordered) == 0: completed = True
                            for hop in l1hopsordered:
                                for k4, v4 in v3.get('L1 Hops').items():
                                    tmpnodes = []
                                    for k5, v5 in v4.get('Nodes').items():
                                        tmpnodes.append(k5)
                                    if (hop[0] == tmpnodes[0] and hop[1] == tmpnodes[1]) or \
                                            (hop[0] == tmpnodes[1] and hop[1] == tmpnodes[0]):
                                        tmphops.append(v4)
                                        l1hopsordered.remove(hop)
                                        break
                                break
                        v3['Ordered L1 Hops'] = tmphops
                        v3.pop('L1 Hops')
                        # logging.info "next L1 hop..."
    with open("jsonfiles/l3Links_final.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def returnorderedlist(firstnode, l1hops):
    l1hopsordered = []
    hopa = firstnode
    hopb = ""
    completed = False
    loopcount = 0
    while not completed:
        if len(l1hops) == 0: completed = True
        for hop in l1hops:
            if len(hop) != 2:
                logging.warn("Invalid L1 hop!  Could not process L1 hops!")
                return None
            elif hop[0] == firstnode or hop[1] == firstnode:
                l1hopsordered.insert(0, hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif (hopa == hop[0] or hopb == hop[1]) or (hopa == hop[1] or hopb == hop[0]):
                l1hopsordered.append(hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif loopcount > 200:
                logging.warn("Could not process L1 hops!")
                return None
            loopcount += 1
    return l1hopsordered


def process_vcfdn_odu_service(vcfdn_dict):
    och_trails = collectmultilayerroute_odu_service_json(vcfdn_dict['baseURL'], vcfdn_dict['epnmuser'], vcfdn_dict['epnmpassword'],
                                         vcfdn_dict['vcfdn'])
    return och_trails


def collectmultilayerroute_odu_service_json(baseURL, epnmuser, epnmpassword, vcfdn):
    logging.info("Making API call to collect multi_layer route for ODU service vc fdn " + vcfdn)
    uri = "/data/v1/cisco-resource-network:virtual-connection-multi-layer-route?vcFdn=" + vcfdn
    jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
    
    try:
        with open("jsongets/multilayer_route_" + vcfdn + ".json", 'wb') as f:
            f.write(jsonresponse)
            f.close()

        with open("jsongets/multilayer_route_" + vcfdn + ".json", 'rb') as f:
            jsonresponse = f.read()
            f.close()
    except Exception as err:
        logging.warn("Could not save or open file for multilayer route odu service for vcFDN " + vcfdn)
        logging.warn("Check this vcFdn and debug with EPNM team if necessary.")

    logging.info("Parsing multilayer_route results for vcFdn " + vcfdn)
    
    try:
        multilayer_route = json.loads(jsonresponse)
        odu_service_route_data = {}
        odu_service_otu_link_list = []
        if multilayer_route['com.response-message']['com.data']:
            if multilayer_route['com.response-message']['com.data']['topo.virtual-connection-multi-layer-route-list'].has_key('topo.virtual-connection-multi-layer-route'):
                for layer in multilayer_route['com.response-message']['com.data']['topo.virtual-connection-multi-layer-route-list'] \
                    ['topo.virtual-connection-multi-layer-route']:
                    subtype = layer['topo.topology-layer']
                    if subtype == "topo:otu-link-layer":
                        try:
                            topo_links = layer['topo.tl-list']['topo.topological-link']
                        except Exception as err:
                            logging.warning("Could not process multi-layer route response, skipping this fdn...")
                            break
                        if isinstance(topo_links, list):
                            odu_service_route_data['vcfdn'] = vcfdn
                            for tl in topo_links:
                                odu_service_otu_link_list.append(tl['topo.fdn'])
                            odu_service_route_data['otu-links'] = odu_service_otu_link_list
                            return odu_service_route_data
                        else:
                            tl = layer['topo.tl-list']['topo.topological-link']
                            odu_service_route_data['vcfdn'] = vcfdn
                            odu_service_otu_link_list.append(tl['topo.fdn'])
                            odu_service_route_data['otu-links'] = odu_service_otu_link_list
                            return odu_service_route_data
                            # list_length = len(topo_links)
                            # och_trail_index = list_length - 1
                            # odu_service_och_trail_data['och-trail-fdn'] = topo_links[och_trail_index]['topo.fdn']
                            # odu_service_och_trail_data['vcfdn'] = vcfdn
                            # return odu_service_och_trail_data

                            # for tl in topo_links:
                            #     tmpfdn = tl['topo.fdn']
                            #     try:
                            #         endpointlist = subitem['topo.endpoint-list']['topo.endpoint']
                            #     except Exception as err:
                            #         logging.error(
                            #             "No endpoint-list or valid endpoints found in the " + topologylayer + " for this vcFdn!")
                            #         l1hops = {}
                            #         return l1hops
    except Exception as err:
        logging.info("Multilayer_route results for vcFdn " + vcfdn + "were missing and couldn't be parsed")


def collect_termination_points_threaded(baseURL, epnmuser, epnmpassword, state_or_states):
    for state in state_or_states:
        with open("jsonfiles/{state}_l3Links_add_tl.json".format(state=state.replace(' ', '_')), 'rb') as f:
            l3links = json.load(f)
            f.close()
        tpfdns = []
        for k1, v1 in l3links.items():
            # logging.info "**************Nodename is: " + k1
            for k2, v2 in v1.items():
                if isinstance(v2, dict):
                    for k3, v3 in v2.items():
                        # logging.info "***************Linkname is: " + k3
                        # if 'vc-fdn' in v3 and not ('Ordered L1 Hops' in v3):
                        #     tpfdn = "MD=CISCO_EPNM!ND=" + k1 + "!FTP=name=" + v3['Local Intf'] + ";lr=lr-ethernet"
                        # else:
                        #     tpfdn = "MD=CISCO_EPNM!ND=" + k1 + "!FTP=name=" + v3['Local Intf'] + ";lr=" + v3['lr type']
                        tpfdn = "MD=CISCO_EPNM!ND=" + k1 + "!FTP=name=" + v3['Local Intf'] + ";lr=" + v3['lr type']
                        logging.info("Node " + k1 + " " + k3 + " tpFdn is " + tpfdn)
                        tpfdn_dict = {'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword,
                                    'tpfdn': tpfdn}
                        v3['tpfdn'] = tpfdn
                        if not tpfdn_dict in tpfdns:
                            tpfdns.append(tpfdn_dict)

        logging.info("Spawning threads to collect termination points...")
        pool = ThreadPool(wae_api.thread_count)
        termination_points = pool.map(process_tpfdn, tpfdns)
        pool.close()
        pool.join()

        for k1, v1 in l3links.items():
            # logging.info "**************Nodename is: " + k1
            for k2, v2 in v1.items():
                if isinstance(v2, dict):
                    for k3, v3 in v2.items():
                        # logging.info "***************Linkname is: " + k3
                        tpfdn = v3['tpfdn']
                        for tp in termination_points:
                            if tp['tpfdn'] == tpfdn:
                                v3['tp-description'] = tp['tp-description']
                                v3['tp-mac'] = tp['tp-mac']
                                v3['tp-mtu'] = tp['tp-mtu']
                                break

        with open("jsonfiles/{state}_l3Links_final.json".format(state=state.replace(' ', '_')), "wb") as f:
            f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
            f.close()


def process_tpfdn(tpfdn_dict):
    l1hops = collect_termination_point(tpfdn_dict['baseURL'], tpfdn_dict['epnmuser'], tpfdn_dict['epnmpassword'],
                                       tpfdn_dict['tpfdn'])
    return l1hops


def collect_termination_point(baseURL, epnmuser, epnmpassword, tpfdn):
    try:
        logging.info("Making API call to collect termination point for tpFdn " + tpfdn)
        uri = "/data/v1/cisco-resource-ems:termination-point?fdn=" + tpfdn
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)

        filename = "jsongets/tp-data-" + tpfdn.split('!')[1] + tpfdn.split('!')[2].split(';')[0].replace('/',
                                                                                                         '-') + ".json"
        logging.info("Filename is " + filename)
        with open(filename, 'wb') as f:
            f.write(jsonresponse)
            f.close()
        with open(filename, 'rb') as f:
            thejson = json.load(f)
            f.close()

        logging.info("Parsing termination_point results for vcFdn " + tpfdn)

        tp_description = ""
        try:
            tp_description = thejson['com.response-message']['com.data']['tp.termination-point']['tp.description']
        except Exception as err:
            logging.warn("termination point " + tpfdn + " not configured with description!")
        try:
            tp_mac_addr = thejson['com.response-message']['com.data']['tp.termination-point']['tp.mac-address']
        except Exception as err:
            logging.warn("Could not get mac-address for tpFdn " + tpfdn)
            tp_mac_addr = ""
        try:
            tp_mtu = str(thejson['com.response-message']['com.data']['tp.termination-point']['tp.mtu'])
        except Exception as err:
            logging.warn("Could not get MTU for tpFdn " + tpfdn)
            tp_mtu = ""
        return {'tpfdn': tpfdn, 'tp-description': tp_description, 'tp-mac': tp_mac_addr, 'tp-mtu': tp_mtu}
    except Exception as err:
        logging.warn("Could not get termination point for tpfdn " + tpfdn)
        logging.warn(err)
        return {'tpfdn': tpfdn, 'tp-description': "", 'tp-mac': "", 'tp-mtu': ""}

def collectlsps_json_new(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-service-network:virtual-connection?type=mpls-te-tunnel"
    jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
    jsonaddition = json.loads(jsonresponse)
    with open("jsongets/vc-mpls-te-tunnel.json", 'wb') as f:
        f.write(json.dumps(jsonaddition, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/vc-mpls-te-tunnel.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    lsplist = []
    vcdict = {}

    for item in thejson['com.response-message']['com.data']['vc.virtual-connection']:
        tmpfdn = None
        adminstate = None
        affinitybits = None
        affinitymask = None
        # destinationIP = None
        tunnelID = None
        tunnelsource = None
        tunneldestination = None
        corouted = None
        signalledBW = None
        fastreroute = None
        adminstate = None
        fdn = None
        erroredlsp = False
        autoroute = None
        # Fix - GLH - 2-18-19 #
        setupPriority = None
        holdPriority = None
        # Fix - GLH - 2-18-19 #
        adminstate = item['vc.admin-state']
        fdn = item['vc.fdn']
        if adminstate == "com:admin-state-up":
            direction = item['vc.direction']
            vcdict['fdn'] = fdn
            vcdict['direction'] = direction
            logging.info("Collecting LSP: " + fdn)
            try:
                term_point = item['vc.termination-point-list']['vc.termination-point']
            except Exception as err:
                logging.warn("LSP does not have valid termination points!  Will not be included in plan.")
                continue
            if isinstance(term_point, dict):
                try:
                    tmpfdn = item['vc.termination-point-list']['vc.termination-point']['vc.fdn']
                except Exception as err:
                    logging.warn("LSP has no vc.fdn, skipping this LSP...")
                    continue
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point']['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                try:
                    signalledBW = subsubsubitem['vc.signalled-bw']
                except Exception as err:
                    logging.warn("Exception: LSP missing signalled-bw attribute, setting to 0 for " + fdn)
                # destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                # Fix - GLH - 2-18-19 #
                setupPriority = subsubsubitem["vc.setup-priority"]
                holdPriority = subsubsubitem["vc.hold-priority"]
                # Fix - GLH - 2-18-19 #
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True
            else:
                logging.info("List format term_point " + fdn)
                try:
                    tmpfdn = item['vc.termination-point-list']['vc.termination-point'][0]['vc.fdn']
                except Exception as err:
                    logging.warn("LSP has no vc.fdn, skipping this LSP...")
                    continue
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point'][0]['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                signalledBW = subsubsubitem['vc.signalled-bw']
                # destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                # Fix - GLH - 2-18-19 #
                holdPriority = subsubsubitem["vc.hold-priority"]
                setupPriority = subsubsubitem["vc.setup-priority"]
                # Fix - GLH - 2-18-19 #
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True

            if not erroredlsp:
                vcdict['admin-state'] = adminstate
                vcdict['tufdn'] = tmpfdn
                vcdict['affinitybits'] = affinitybits
                vcdict['affinitymask'] = affinitymask
                # vcdict['Destination IP'] = destinationIP
                vcdict['Tunnel ID'] = tunnelID
                vcdict['Tunnel Source'] = tunnelsource
                vcdict['Tunnel Destination'] = tunneldestination
                vcdict['co-routed'] = corouted
                vcdict['signalled-bw'] = signalledBW
                vcdict['FRR'] = fastreroute
                vcdict['auto-route-announce-enabled'] = autoroute
                # Fix - GLH - 2-18-19 #
                vcdict["vc.hold-priority"] = holdPriority
                vcdict["vc.setup-priority"] = setupPriority
                # Fix - GLH - 2-18-19 #
                lsplist.append(vcdict)
                logging.info(
                    "Collected tunnel " + str(
                        tunnelID) + " Source: " + tunnelsource + " Destination " + tunneldestination)
            else:
                logging.warn("Could not retrieve necessary attributes.  LSP will be left out of plan: " + fdn)
            vcdict = {}
        else:
            logging.warning("Tunnel unavailable: " + fdn)
    logging.info("Completed collecting LSPs...")
    with open("jsonfiles/lsps.json", "wb") as f:
        f.write(json.dumps(lsplist, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
        
        
def collectlsps_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-service-network:virtual-connection?type=mpls-te-tunnel&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
            merge(jsonmerged, jsonaddition)
        elif lastindex == -1:
            incomplete = False
        else:
            incomplete = False
            merge(jsonmerged, jsonaddition)

    with open("jsongets/vc-mpls-te-tunnel.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/vc-mpls-te-tunnel.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    lsplist = []
    vcdict = {}

    for item in thejson['com.response-message']['com.data']['vc.virtual-connection']:
        tmpfdn = None
        adminstate = None
        affinitybits = None
        affinitymask = None
        # destinationIP = None
        tunnelID = None
        tunnelsource = None
        tunneldestination = None
        corouted = None
        signalledBW = None
        fastreroute = None
        adminstate = None
        fdn = None
        erroredlsp = False
        autoroute = None
        # Fix - GLH - 2-18-19 #
        setupPriority = None
        holdPriority = None
        # Fix - GLH - 2-18-19 #
        adminstate = item['vc.admin-state']
        fdn = item['vc.fdn']
        if adminstate == "com:admin-state-up":
            direction = item['vc.direction']
            vcdict['fdn'] = fdn
            vcdict['direction'] = direction
            logging.info("Collecting LSP: " + fdn)
            try:
                term_point = item['vc.termination-point-list']['vc.termination-point']
            except Exception as err:
                logging.warn("LSP does not have valid termination points!  Will not be included in plan.")
                continue
            if isinstance(term_point, dict):
                try:
                    tmpfdn = item['vc.termination-point-list']['vc.termination-point']['vc.fdn']
                except Exception as err:
                    logging.warn("LSP has no vc.fdn, skipping this LSP...")
                    continue
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point']['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                try:
                    signalledBW = subsubsubitem['vc.signalled-bw']
                except Exception as err:
                    logging.warn("Exception: LSP missing signalled-bw attribute, setting to 0 for " + fdn)
                # destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                # Fix - GLH - 2-18-19 #
                setupPriority = subsubsubitem["vc.setup-priority"]
                holdPriority = subsubsubitem["vc.hold-priority"]
                # Fix - GLH - 2-18-19 #
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True
            else:
                logging.info("List format term_point " + fdn)
                try:
                    tmpfdn = item['vc.termination-point-list']['vc.termination-point'][0]['vc.fdn']
                except Exception as err:
                    logging.warn("LSP has no vc.fdn, skipping this LSP...")
                    continue
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point'][0]['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                signalledBW = subsubsubitem['vc.signalled-bw']
                # destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                # Fix - GLH - 2-18-19 #
                holdPriority = subsubsubitem["vc.hold-priority"]
                setupPriority = subsubsubitem["vc.setup-priority"]
                # Fix - GLH - 2-18-19 #
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True

            if not erroredlsp:
                vcdict['admin-state'] = adminstate
                vcdict['tufdn'] = tmpfdn
                vcdict['affinitybits'] = affinitybits
                vcdict['affinitymask'] = affinitymask
                # vcdict['Destination IP'] = destinationIP
                vcdict['Tunnel ID'] = tunnelID
                vcdict['Tunnel Source'] = tunnelsource
                vcdict['Tunnel Destination'] = tunneldestination
                vcdict['co-routed'] = corouted
                vcdict['signalled-bw'] = signalledBW
                vcdict['FRR'] = fastreroute
                vcdict['auto-route-announce-enabled'] = autoroute
                # Fix - GLH - 2-18-19 #
                vcdict["vc.hold-priority"] = holdPriority
                vcdict["vc.setup-priority"] = setupPriority
                # Fix - GLH - 2-18-19 #
                lsplist.append(vcdict)
                logging.info(
                    "Collected tunnel " + str(
                        tunnelID) + " Source: " + tunnelsource + " Destination " + tunneldestination)
            else:
                logging.warn("Could not retrieve necessary attributes.  LSP will be left out of plan: " + fdn)
            vcdict = {}
        else:
            logging.warning("Tunnel unavailable: " + fdn)
    logging.info("Completed collecting LSPs...")
    with open("jsonfiles/lsps.json", "wb") as f:
        f.write(json.dumps(lsplist, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def parseintfnum(nodeintf):
    nodeintfnum = ""
    intflist = ['HundredGigE', 'TenGigE', 'FortyGigE', 'Optics']
    returnstring = ""
    for i in intflist:
        try:  # this block is for Ethernet interfaces
            nodeintfnum = re.search('.*%s(.*)\..*' % (i), nodeintf).group(1)
            break
        except:
            pass
        try:  # this block is for "Optics" interfaces
            nodeintfnum = re.search('.*%s(.*).*' % (i), nodeintf).group(1)
            break
        except:
            pass
    try:
        re.search('%s(.*).*' % ('BDI'), nodeintf).group(1)
        nodeintfnum = nodeintf
        return nodeintfnum
    except:
        pass
    if nodeintfnum == "":
        logging.info("Could not parse interface number!!!!!!!!!")
    else:
        if len(nodeintfnum.split('/')) == 5:
            shortnodeintfnum = nodeintfnum.split('/')[:-1]
        else:
            shortnodeintfnum = nodeintfnum.split('/')
        for num in shortnodeintfnum:
            returnstring += num + "/"

    return returnstring[:-1]


def parseintftype(nodeintf):
    nodeintfnum = ""
    nodeintftype = ""
    intflist = ['HundredGigE', 'TenGigE', 'FortyGigE']
    intf_lr_list = ['lr-hundred-gigabit-ethernet', 'lr-ten-gigabit-ethernet', 'lr-forty-gigabit-ethernet']
    intf_bw_list = [100000, 10000, 40000]
    for i in intflist:
        try:  # this block is for Ethernet interfaces
            nodeintfnum = re.search('.*%s(.*)\..*' % (i), nodeintf).group(1)
            nodeintftype = i
            nodeintf_lr_type = intf_lr_list[intflist.index(i)]
            nodeintf_bw = intf_bw_list[intflist.index(i)]
            break
        except:
            pass
        try:  # this block is for "Optics" interfaces
            nodeintfnum = re.search('.*%s(.*).*' % (i), nodeintf).group(1)
            nodeintftype = i
            nodeintf_lr_type = intf_lr_list[intflist.index(i)]
            nodeintf_bw = intf_bw_list[intflist.index(i)]
            break
        except:
            pass
    try:
        re.search('%s(.*).*' % ('BDI'), nodeintf).group(1)
        nodeintfnum = nodeintf
        nodeintftype = 'BDI'
        nodeintf_lr_type = 'lr-bridge'
        nodeintf_bw = 0
        return nodeintftype, nodeintf_lr_type, nodeintf_bw
    except:
        pass
    if nodeintfnum == "":
        logging.info("Could not parse interface type!!!!!!!!!")
        return None
    else:
        return nodeintftype, nodeintf_lr_type, nodeintf_bw


def merge(a, b):
    "merges b into a"
    for key in b:
        if key in a:  # if key is in both a and b
            if isinstance(a[key], dict) and isinstance(b[key], dict):  # if the key is dict Object
                merge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key] = a[key] + b[key]
        else:  # if the key is not in dict a , add it to dict a
            a.update({key: b[key]})
    return a
