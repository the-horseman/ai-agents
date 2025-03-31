from langchain_core.tools import tool
from ..utils.request import make_request
from ..utils.constants import *


@tool
def get_details_on_indicators_of_compromise(ioc: str, fields: str) -> str:
    """
    Use this to get the details about the current ioc. You must use the supported fields as they are mentioned. This tool should be called parallely in a single tool_call.

    This tool should be called in parallel for all the IOCs that you find.
     
    Args:
        ioc (str): The indicator of compromise that was found in the current set of events that you want to find campaign details about. Types of Supported IOCs are - MD5, SHA256, SHA512, URL, IP, Domain, Hostname
        fields (str) : Comma seperated feilds that you want the details about. Supported Fields are - campaigns, threat, lethality, prevalence, determinism
        
    Returns:
        str: The details that were requested on the IOC.
    """
    try:
        url = f"{INSIGHTS_API_BASE_URL}/iocs"
        params = {
            "filter.value.like" : ioc,
            "limit":10,
            "fields":f"type,value,id,category,{''.join(fields.split())}"
        }
        response = make_request(url=url, params=params)
        return response.text
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"
    
@tool
def get_file_details_for_indicators_of_compromise(hash_value: str):
    """
    Use this to get the details about the file. This tool should be called paralelly in a single tool_call.

    This tool should be called in parallel for all the IOCs that you find.
    
    Args:
        hash_value (str): The hash value of the file that you want to find details about. The hash can only be a SHA256 hash.
        
    Returns:
        str: The details that were requested on the file.
    """
    try:
        url = f"{INSIGHTS_API_BASE_URL}/artefacts/files"
        params = {
            "hashvalue" : hash_value,
            "hashtype": "sha256",
            "fields": "campaigns"
        }
        response = make_request(url=url, params=params)
        return response.text
    except BaseException as e:
        return f"Could not complete request because following Exception occured: {str(e)}"


insight_tools = [get_file_details_for_indicators_of_compromise,get_details_on_indicators_of_compromise]