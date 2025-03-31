import httpx
import json
import time
from datetime import datetime, timedelta
from .constants import *


def get_login_token(cached: bool):
    """
    This function gets a login token from the Trellix Insights API.
    
    Args:
        cached (bool): Whether to use a cached token or get a new one.
    
    Returns:
        str: The login token.
    """
    file_path = "token.txt"
    if not cached:
        response = httpx.post(
            url=IAM_TOKEN_URL, 
            params={
                "grant_type": "password",
                "scope": INSIGHT_SCOPES,
                "username":TENANT_USERNAME,
                "password": TENANT_PASSWORD,
                "client_id":"0oae8q9q2y0IZOYUm0h7"
            },
            verify=False)
        auth_token = "Bearer " + response.json()["access_token"]
        with open(file_path, "w+") as f:
            f.write(auth_token)
    else:
        with open(file_path, "r+") as f:
            auth_token = f.read().strip()
    return auth_token
        

def make_request(url: str, params: dict={}, headers: dict={}):
    """
    This function makes a request to the Trellix Insights API.
    
    Args:
        url (str): The URL of the API endpoint.
        params (dict, optional): The parameters to be passed to the API. Defaults to {}.
        headers (dict, optional): The headers to be passed to the API. Defaults to {}.
    
    Returns:
        Response: The response from the API.
    """
    print(f"MAke request : url:{url} params:{params}")
    response = httpx.get(
        url=url,
        headers={
            "Authorization" : get_login_token(cached=True),
            **headers
        },
        params=params,
        verify=False
    )
    if response.status_code == 401:
        response = httpx.get(
            url=url,
            headers={
                "Authorization" : get_login_token(cached=False),
                **headers
            },
            params=params,
            verify=False
        )
    print(f"MAke request : res: {response}")
    return response


def make_historical_request(condition:dict, date_of_detection:str, date_range:int):
    """
    This function makes a request to the Trellix Historical Search API.
    
    Args:
        condition (dict): The condition to be used for the historical search.
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58.
        date_range (int): The number of days to look back for historical data.
    
    Returns:
        Response: The response from the API.
    """
    #date_of_detection = "2024-10-28 08:40:49"
    search_headers = {
            "X-Auth-TenantId": TENANT_ID,
            "Content-Type": "application/vnd.api+json",
            "Authorization": AUTH
        }
    date_of_detection = datetime.strptime(date_of_detection, "%Y-%m-%d %H:%M:%S")
    request_body = {
            "data": {
                "type": "search",
                "attributes": {
                "query": {
                        "projections": [{
                            "name": "AllEvents"
                        }],
                        "condition": condition,
                        "fromDate": (date_of_detection - timedelta(days=date_range)).timestamp()*1000,
                        "toDate": (date_of_detection + timedelta(hours=4)).timestamp()*1000
                    }
                }
            }
        }
    #print(json.dumps(request_body, indent=2))
    response = httpx.post(
        url=f"{HISTORICAL_API_BASE_URL}/historicalsearch",
        json=request_body,
        headers=search_headers,
        verify=False
    )
    while response.json()["data"]["attributes"]["status"] != "SUCCESS":
        response = httpx.get(
            url=f"{HISTORICAL_API_BASE_URL}/searches/{response.json()['data']['id']}/status",
            headers=search_headers,
            verify=False
        )
        time.sleep(2)
    response = httpx.get(
            url=f"{HISTORICAL_API_BASE_URL}/searches/{response.json()['data']['id']}/results?sort=-Time&page[limit]=10",
            headers=search_headers,
            verify=False
        )
    return response


def make_rts_request(device_name: str, rts_projection: str):
    """
    This function makes a request to the Trellix Real-Time Search API.
    
    Args:
        device_name (str): The name of the device to search for.
        rts_projection (str): The projection to be used for the search.
    
    Returns:
        Response: The response from the API.
    """
    rts_headers = {
        "Authorization" : AUTH,
        "X-Tenant-Id" : TENANT_ID
    }
    response = httpx.post(
        url=f"{RTS_API_BASE_URL}/searches", 
        json={
            "projections": [
                {
                    "name": rts_projection
                }
            ],
            "condition": {
                "or": [
                    {
                        "and": [
                            {
                                "name": "HostInfo",
                                "output": "hostname",
                                "op": "EQUALS",
                                "value": device_name
                            }
                        ]
                    }
                ]
            },
            "aggregated": True
        },
        headers=rts_headers,
        verify=False
    )
    rts_id = response.json()["id"]
    response = httpx.get(
        url=f"{RTS_API_BASE_URL}/searches/{rts_id}/status",
        headers=rts_headers,
        verify=False
    )
    while response.json()["status"] != "FINISHED":
        response = httpx.get(
            url=f"{RTS_API_BASE_URL}/searches/{rts_id}/status",
            headers=rts_headers,
            verify=False
        )
        time.sleep(2)
    response = httpx.get(
        url=f"{RTS_API_BASE_URL}/searches/{rts_id}/results",
        headers=rts_headers,
        verify=False
    )
    return response


def check_device_online_rts(device_name):
    try:
        device_avail_response = make_rts_request(device_name=device_name, rts_projection="HostInfo")
        if device_avail_response.json()["items"][0]["output"]["HostInfo|connection_status"] == "Online":
            return True
        return False
    except:
        return False


def add_filters_to_hs(filter_dict:dict, base_condition:dict):
    for key in filter_dict.keys():
        base_condition.append(
            {
                "name": "AllEvents",
                "output": key,
                "op": "CONTAINS",
                "negated": False,
                "value": str(filter_dict[key]).replace('\\', '\\\\')
            }
        )
    return base_condition


def make_detections_request(condition:dict, date_of_detection:str, date_range:int):
    """
    This function makes a request to the Trellix Historical Detections API.
    
    Args:
        condition (dict): The condition to be used for the historical search.
        date_of_detection (str): The date of detection in YYYY-MM-DD %H:%M:%S Format. example : 2024-08-26 12:56:58.
        date_range (int): The number of days to look back for historical data.
    
    Returns:
        Response: The response from the API.
    """
    search_headers = {
            "X-Auth-TenantId": TENANT_ID,
            "Content-Type": "application/vnd.api+json",
            "Authorization": AUTH
        }
    date_of_detection = datetime.strptime(date_of_detection, "%Y-%m-%d %H:%M:%S")
    request_body = {
            "data": {
                "type": "search",
                "attributes": {
                "query": {
                        "projections": [{
                            "name": "AllEvents"
                        }],
                        "condition": condition,
                        "fromDate": (date_of_detection - timedelta(days=date_range)).timestamp()*1000,
                        "toDate": (date_of_detection + timedelta(hours=4)).timestamp()*1000
                    }
                }
            }
        }
    #print(json.dumps(request_body, indent=2))
    response = httpx.post(
        url=f"{HISTORICAL_API_BASE_URL}/detections?page[limit]=10",
        json=request_body,
        headers=search_headers,
        verify=False
    )
    return response