import json
from pprint import pprint
import re
import logging
import os
import random


def get_tl_mpls_ep_ref_nodes():
    tl_mpls_endpoint_ref_nodes = []
    tl_links_dict = open_file_load_data('jsongets/tl-mpls-link-layer.json')
    for endpoint in tl_links_dict["com.response-message"]["com.data"]["topo.topological-link"]:
        if "topo.endpoint-list" in endpoint.keys():
            for endpoint_ref in endpoint["topo.endpoint-list"]["topo.endpoint"]:
                tl_mpls_endpoint_ref_nodes.append(endpoint_ref['topo.endpoint-ref'].split('=')[2].split('!')[0])
    return list(set(tl_mpls_endpoint_ref_nodes))


def get_seed_nodes():
    json_list = []
    nodes_4k_dict = open_file_load_data('jsongets/4k-nodes.json')
    for node in nodes_4k_dict["com.response-message"]["com.data"]["nd.node"]:
        tmp_master = {}
        tmp_master["node"] = node["nd.fdn"]
        tmp_master['group'] = node["nd.group"]
        json_list.append(tmp_master)
    return json_list


def run_get_4k_seed_nodes():
    all_mpls_nodes = get_tl_mpls_ep_ref_nodes()
    all_potential_seed_nodes = get_seed_nodes()
    final_mpls_seed_node_list = []
    for seed_node_object in all_potential_seed_nodes:
        if seed_node_object['node'].split('=')[-1] in all_mpls_nodes:
            final_mpls_seed_node_list.append(seed_node_object)
    write_results("jsonfiles/all_potential_seed_nodes.json", final_mpls_seed_node_list)


def get_potential_seednode(state_or_states):
    final_seed_node_dict = open_file_load_data('jsonfiles/all_potential_seed_nodes.json')
    if isinstance(state_or_states, list):
        for state in state_or_states:
            tmp = {}
            tmp[state] = [json_obj for json_obj in final_seed_node_dict if json_obj['group'][-1].split('=')[-1] in state]
            file_name = "jsonfiles/{state}_potential_seed_nodes.json".format(state=state.replace(' ', '_'))
            write_results(file_name, tmp)


def write_results(file_name, data):
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as f:
        f.write(json.dumps(data, f, sort_keys=True, indent=4, separators=(',', ': ')))

def open_file_load_data(file_name):
    with open(file_name, 'rb') as f:
        data = json.loads(f.read())
    return data

def get_random_seed_node(seed_node_list):
    try:
        return random.choice(seed_node_list)
    except IndexError:
        pass


def get_random_nodes_for_states(state_or_states):
    random_node_choices = []
    for state in state_or_states:
        seed_nodes = open_file_load_data("jsonfiles/{state}_potential_seed_nodes.json".format(state=state.replace(' ', '_')))
        seed_node_choice = get_random_seed_node(seed_nodes[state])
        random_node_choices.append(seed_node_choice)
    return [node for node in random_node_choices if node != None]

if __name__ == "__main__":
    ### System Arguments ###
    state_or_states = ['All Locations']
    ########################################
    
    run_get_4k_seed_nodes()
    get_potential_seednode(state_or_states)
    print (get_random_nodes_for_states(state_or_states))