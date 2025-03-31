from json import dump


def transform_traces(traces:list[dict]):
    """
    This function takes a list of traces and transforms them into a list of dictionaries.
    The dictionaries contain the following information:
        - SHA256: The SHA256 hash of the file.
        - severity: The severity of the event.
        - time: The time of the event.
        - process_id: The process ID of the process that executed the file.
        - parent_process_id: The parent process ID of the process that executed the file.
        - command_line: The command line used to execute the file.
        - process_name: The name of the process.
        - host_os: The operating system of the host.
        - user_name: The name of the user that executed the file.
    
    Args:
        traces (list[dict]): A list of traces.
    
    Returns:
        list[dict]: A list of dictionaries containing the transformed traces.
    """
    transformed_traces = []
    sha256_list = []
    for ind, cur in enumerate(traces):
        event_type = cur["eventType"].split()[0].lower()
        # cur_hash = hash(str({cur["pSha2"], event_type}))
        # if cur_hash not in sha256_list:
        #     sha256_list.append(cur_hash)
        transformed_traces.append({"SHA256": cur["pSha2"]})
        transformed_traces[-1]["event_type"] = cur["eventType"]
        transformed_traces[-1]["severity"] = cur.get("severity")
        transformed_traces[-1]["time"] = cur.get("time")
        transformed_traces[-1]["process_id"] = cur.get("pid")
        transformed_traces[-1]["parent_process_id"] = cur.get("ppid")
        transformed_traces[-1]["host_os"] = cur.get("h_os")
        event_specific_fields = get_event_specific_fields(trace=cur, event_type=event_type)
        transformed_traces[-1] = {**transformed_traces[-1], **event_specific_fields}
    transformed_traces = sorted(transformed_traces, key=lambda x: x["time"])
    #with open("aryan.json", "w+") as f:
        #dump(transformed_traces, fp=f, indent=4)
    return transformed_traces

def get_event_specific_fields(trace, event_type):
    if event_type == "process":
        return {
            'process_details' : trace.get('procFileAttrs'), 
            'user_name': trace.get('user')["name"] if trace.get("user") else None
        }
    elif event_type == "network":
        return {"connection_details" : trace.get("network")}
    elif event_type == 'api':
        return {"api_details" : trace.get("api")}
    elif event_type == 'regvalue':
        return {'registry_details' : trace.get('registry')}
    elif event_type == 'image':
        return {'module_details' : trace.get('modules')}
    elif event_type == 'file':
        return {'file_details' : trace.get('fileAttributes')}
    # elif event_type == 'script':
    #     return {
    #         'script_type' : trace.get('scriptType'), 
    #         'scripts' : trace.get('scripts')
    #     }
    elif event_type == 'dns':
        return {"dsn_details": trace.get('dns')}
    else:
        return {}


def transform_hs_response(events: dict):
    """
    This function takes a list of events and transforms them into a list of dictionaries.
    
    Args:
        events (list[dict]): A list of events.
    
    Returns:
        list[dict]: A list of dictionaries containing the transformed events.
    """
    transformed_events = []
    for event in events:
        event = event["output"]
        transformed_event = {}
        for key in event.keys():
            transformed_event[key.split('|')[-1]] = event[key]
        transformed_events.append(transformed_event)
    return transformed_events