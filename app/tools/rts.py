
import json
from langchain_core.tools import tool

from ..utils.request import check_device_online_rts, make_rts_request

@tool
def get_browser_downloads(device_name:str):
    """
    Use this tool to get the downloads done from any browser for the selected device.

    Args:
        device_name (str): The name of the device that you want to get the downloads for.

    Returns:
        str: The details that were requested on the file.
    """
    if not check_device_online_rts(device_name):
        return "The device is not online and hence no Real Time Data could be found. \nThis will happen for all the Real Time Queries hence do not use any Real Time leads for now."
    reponse = make_rts_request(device_name=device_name, rts_projection="BrowserDownload")
    return json.dumps(obj=reponse.json()["items"], indent=1)

@tool
def get_current_network_data(device_name:str):
    """
    Use this tool to get the current network data for the selected device.

    Args:
        device_name (str): The name of the device that you want to get the network data for.
        
    Returns:
        str: The details that were requested on the file.
    """
    if not check_device_online_rts(device_name):
        return "The device is not online and hence no Real Time Data could be found. \nThis will happen for all the Real Time Queries hence do not use any Real Time leads for now."
    reponse = make_rts_request(device_name=device_name, rts_projection="CurrentFlow")
    return json.dumps(obj=reponse.json()["items"], indent=1)

@tool
def get_installed_softwares(device_name:str):
    """
    Use this tool to get the installed softwares for the selected device.
    
    Args:
        device_name (str): The name of the device that you want to get the installed softwares for.
        
    Returns:
        str: The details that were requested on the file.
    """
    if not check_device_online_rts(device_name):
        return "The device is not online and hence no Real Time Data could be found. \nThis will happen for all the Real Time Queries hence do not use any Real Time leads for now."
    reponse = make_rts_request(device_name=device_name, rts_projection="Software")
    return json.dumps(obj=reponse.json()["items"], indent=1)

rts_tools = [get_browser_downloads, get_current_network_data, get_installed_softwares]
