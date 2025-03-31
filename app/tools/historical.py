import json
from langchain_core.tools import tool

from ..utils.request import add_filters_to_hs, make_historical_request, make_detections_request
from ..utils.transform import transform_hs_response

@tool
def get_historical_process_data(date_of_detection:str, process_dict: dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical process data for a given process dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        process_dict (dict): The process dictionary. All the keys are optional. Keys supported in the dict - 
            1. ProcessName : procFileAttrs.name
            2. Process_Sha256 : procFileAttrs.Sha256
            3. Pid : process_id
            4. Ppid : parent_process_id
            5. CommandLine : cmdLine
            6. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical process data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "Process"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=process_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"

@tool
def get_historical_file_data(date_of_detection:str, file_dict: dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical file data for a given file dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        file_dict (dict): The file dictionary. All the keys are optional. Keys supported in the dict - 
            1. File_Name : fileAttributes.name
            2. File_Type : fileAttributes.fileType
            3. File_Sha256 : fileAttributes.Sha256
            4. File_Creation_Date : fileAttributes.creationDate
            5. File_Last_Access_Date : fileAttributes.lastAccessDate
            6. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical file data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "File"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=file_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
            "or" : [
                {"and": base_condition}
            ]
        }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"

@tool
def get_historical_network_data(date_of_detection:str, network_dict:dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical network data for a given network dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        network_dict (dict): The network dictionary. All the keys are optional. Keys supported in the dict - 
            1. IpAddress : network.dstIp
            2. Network_DstPort : network.dstPort
            3. Network_Direction : network.direction
            4. Network_SrcIp : network.srcIp
            5. Network_SrcPort : network.srcPort
            6. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical network data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "Network"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=network_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"

@tool
def get_historical_user_data(date_of_detection:str, user_dict: dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical user data for a given user dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        user_dict (dict): The user dictionary. All the keys are optional. Keys supported in the dict - 
            1. User_Name : user.name
            2. User_Domain : user.domain
            3. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical user data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "User"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=user_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"


@tool
def get_historical_registry_data(date_of_detection:str, registry_dict: dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical registry data for a given registry dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        registry_dict (dict): The registry dictionary. All the keys are optional. Keys supported in the dict - 
            1. Registry_Key_Name : registry.regKeyName
            2. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical registry data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "RegKey"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=registry_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"


@tool
def get_historical_scheduled_tasks_data(date_of_detection:str, schedule_task_dict: dict, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical scheduled tasks data for a given scheduled tasks dictionary and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        schedule_task_dict (dict): The scheduled tasks dictionary. All the keys are optional. Keys supported in the dict - 
            1. SchedTask_Name : schedtask.name
            2. Parent_Process_Name : parent_process_name (only the final process name, not teh full path)
            You must only use the mentioned keys and values to be the mentioned paths from events. 
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical scheduled tasks data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Activity",
            "op": "CONTAINS",
            "negated": False,
            "value": "ScheduledTask"
        }
    ]
    base_condition = add_filters_to_hs(filter_dict=schedule_task_dict, base_condition=base_condition)
    if device_name != None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName":device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_historical_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"


@tool
def get_historical_detections(date_of_detection:str, process_name:str = None, device_name:str = None, date_range:int = 7):
    """
    This tool is used to get the historical detections for a given process name and device name.
    
    Args:
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58. Path in evnets -  detections.firstDetected
        process_name (str, optional): The name of the process. Defaults to None. To search on all processes, you must leave this as None(default).
        device_name (str, optional): The name of the device. Defaults to None. To search on all devices, you must leave this as None(default).
        date_range (int, optional): The number of days to look back for historical data. Defaults to 7.
    
    Returns:
        str: The historical detections data in JSON format.
    """
    base_condition = [
        {
            "name": "AllEvents",
            "output": "Severity",
            "op": "IN",
            "value": "s1,s2,s3,s4,s5"
        }
    ]
    if process_name is not None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"ProcessName": process_name})
    if device_name is not None:
        base_condition = add_filters_to_hs(base_condition=base_condition, filter_dict={"DeviceName": device_name})
    condition = {
        "or" : [
            {"and": base_condition}
        ]
    }
    try:
        response = make_detections_request(condition=condition, date_of_detection=date_of_detection, date_range=date_range)
        hs_response = transform_hs_response(response.json()["data"]["attributes"]["items"])
        return json.dumps(obj=hs_response, indent=1)
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"

historical_tools = [get_historical_file_data, get_historical_process_data, get_historical_network_data, get_historical_user_data,
    get_historical_registry_data, get_historical_scheduled_tasks_data]
detection_tools = [get_historical_detections]