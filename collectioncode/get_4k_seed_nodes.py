## 1.1 = refactored and changed dict methods



import json
from pprint import pprint
import re
import logging
import os
import random
import collect


def get_tl_mpls_ep_ref_nodes():
    tl_links_dict = open_file_load_data('jsongets/tl-mpls-link-layer.json')
    tl_mpls_endpoint_ref_nodes = [endpoint_ref.get('topo.endpoint-ref').split('=')[2].split('!')[0] for endpoint in tl_links_dict.get("com.response-message").get("com.data").get("topo.topological-link") if endpoint.get("topo.endpoint-list") for endpoint_ref in endpoint.get("topo.endpoint-list").get("topo.endpoint")]
    return list(set(tl_mpls_endpoint_ref_nodes))


def get_seed_nodes():
    json_list = []
    nodes_4k_dict = open_file_load_data('jsongets/4k-nodes.json')
    for node in nodes_4k_dict.get("com.response-message").get("com.data").get("nd.node"):
        tmp_master = {}
        tmp_master.setdefault("node", node.get("nd.fdn"))
        tmp_master.setdefault('group', node.get("nd.group"))
        json_list.append(tmp_master)
    return json_list


def run_get_4k_seed_nodes():
    all_mpls_nodes = get_tl_mpls_ep_ref_nodes()
    all_potential_seed_nodes = get_seed_nodes()
    final_mpls_seed_node_list = [seed_node_object for seed_node_object in all_potential_seed_nodes if seed_node_object.get('node').split('=')[-1] in all_mpls_nodes]
    write_results("jsonfiles/all_potential_seed_nodes.json", final_mpls_seed_node_list)


def get_potential_seednode(state_or_states):
    final_seed_node_dict = open_file_load_data('jsonfiles/all_potential_seed_nodes.json')
    if isinstance(state_or_states, list):
        for state in state_or_states:
            tmp = {}
            tmp[state] = [seed_node for seed_node in final_seed_node_dict for item in seed_node.get('group') if state in item.split('=')[-1]]
            for tmp_dict in tmp.items():
                for tmp_node in tmp_dict[1]:
                    tmp_node['state'] = state
            file_name = "jsonfiles/{state}_potential_seed_nodes.json".format(state=state.strip().replace(' ', '_'))
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


def get_random_nodes_for_states(state_or_states):
    random_node_choices = []
    valid_seed_nodes = open_file_load_data("configs/valid_seed_node.json")
    for state in state_or_states:
        state = state.strip()
        if state in valid_seed_nodes:
            node_id = valid_seed_nodes[state]['node']
            collect.thread_data.logger.debug('The seed node ID in the valid_seed_node.json file is: {}'.format(node_id))
            if node_id.startswith('MD'):
                pass
            else: valid_seed_nodes[state]['node'] = "MD=CISCO_EPNM!ND=" + node_id
            random_node_choices.append(valid_seed_nodes[state])
        else:
            seed_nodes = open_file_load_data("jsonfiles/{state}_potential_seed_nodes.json".format(state=state.strip().replace(' ', '_')))
            if seed_nodes.get(state):
                random_node_choices.append(seed_nodes[state])
                collect.thread_data.logger.info('The valid seed-node for {} is: {}'.format(state, random_node_choices[-1]))
    return random_node_choices

if __name__ == "__main__":
    ### System Arguments ###
    state_or_states = ['New York', 'New Jersey']
    ########################################
    
    pprint (get_random_nodes_for_states(state_or_states))
    run_get_4k_seed_nodes()
    get_potential_seednode(state_or_states)
