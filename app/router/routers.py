from typing import Literal

def insight_router(state) -> Literal["call_tool", "continue"]:
    """
    This router determines the next node to execute based on the current state.
    
    Args:
        state (dict): The current state of the graph.
    
    Returns:
        str: The name of the next node to execute.
    """
    last_message = state["messages"][-1]
    if len(last_message.tool_calls) > 0:
        return "call_tool"
    return "__end__"


def supervisor_router(state):
    """
    This router determines the next node to execute based on the current state.
    
    Args:
        state (dict): The current state of the graph.
    
    Returns:
        str: The name of the next node to execute.
    """
    last_message = state["messages"][-1]
    if last_message.further_analysis_required.lower() == "historical":
        return "historical_analysis"
    elif last_message.further_analysis_required.lower() == "real_time":
        return "real_time_analysis"
    elif last_message.further_analysis_required.lower() == "detection":
        return "detection_analysis"
    elif last_message.further_analysis_required.lower() == "ask_human":
        return "ask_human"
    return "__end__"


def historical_router(state):
    """
    This router determines the next node to execute based on the current state.
    
    Args:
        state (dict): The current state of the graph.
    
    Returns:
        str: The name of the next node to execute.
    """
    last_message = state["messages"][-1]
    if len(last_message.tool_calls) > 0:
        return "call_tool"
    return "review_report"


def real_time_router(state):
    """
    This router determines the next node to execute based on the current state.
    
    Args:
        state (dict): The current state of the graph.
    
    Returns:
        str: The name of the next node to execute.
    """
    last_message = state["messages"][-1]
    if len(last_message.tool_calls) > 0:
        return "call_tool"
    return "review_report"


def human_approval_router(state) -> Literal["approved", "further_investigation_needed"]:
    """
    This router determines the next node to execute based on the current state.
    
    Args:
        state (dict): The current state of the graph.
    
    Returns:
        str: The name of the next node to execute.
    """
    last_message = state["messages"][-1]
    if len(last_message.user_approval) > 0 and last_message.user_approval == "approved":
        return "approved"
    return "further_investigation_needed"