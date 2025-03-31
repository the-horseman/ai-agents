from langgraph.graph import StateGraph
from .base import BaseWorkflow, BaseState
import operator
from functools import partial
from langgraph.prebuilt import ToolNode
from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph

from ..tools.historical import historical_tools, detection_tools
from ..tools.rts import rts_tools
from ..agents.questions import historical_agent, supervisor_agent, rts_agent, detections_agent, ask_human_agent, ask_human_response_agent
from ..router.routers import historical_router, supervisor_router, real_time_router
from langgraph.graph import END, START
from ..checkpoint.postgres_saver import HumanApprovalPostgresSaver
from .base import BaseState

class QuestionsWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def create_graph(self, checkpointer : HumanApprovalPostgresSaver ) -> StateGraph:
        
        workflow = StateGraph(BaseState)

        workflow.add_edge(START,"questions_supervisor_agent")    

        supervisor_node = partial(super().agent_node, agent=supervisor_agent, name="questions_supervisor_agent")
        historical_node = partial(super().agent_node, agent=historical_agent, name="historical_agent")
        real_time_node = partial(super().agent_node, agent=rts_agent, name="rts_agent")
        detections_node = partial(super().agent_node, agent=detections_agent, name="detections_agent")
        historical_tool_node = ToolNode(historical_tools)
        real_time_tool_node = ToolNode(rts_tools)
        detections_tool_node = ToolNode(detection_tools)

        ask_human_node = partial(super().agent_node, agent=ask_human_agent, name="ask_human")
        ask_human_response_node = partial(super().agent_node, agent=ask_human_response_agent, name="ask_human_response_agent")

        workflow.add_node("historical_search_tools", historical_tool_node)
        workflow.add_node("questions_supervisor_agent", supervisor_node)
        workflow.add_node("historical_agent", historical_node)
        workflow.add_node("real_time_agent", real_time_node)
        workflow.add_node("real_time_search_tools", real_time_tool_node)
        workflow.add_node("detections_agent", detections_node)
        workflow.add_node("detections_search_tools", detections_tool_node)
        workflow.add_node("ask_human", ask_human_node)
        workflow.add_node("ask_human_response", ask_human_response_node)

        workflow.add_conditional_edges(
            "historical_agent",
            historical_router,
            {"call_tool": "historical_search_tools", "review_report": "questions_supervisor_agent"},
        )
        workflow.add_conditional_edges(
            "questions_supervisor_agent",
            supervisor_router,
            path_map={
                "historical_analysis": "historical_agent", 
                "real_time_analysis": "real_time_agent", 
                "detection_analysis" : "detections_agent", 
                "ask_human":"ask_human",
                "__end__": END
            },
        )
        workflow.add_conditional_edges(
            "real_time_agent",
            real_time_router,
            {"call_tool": "real_time_search_tools", "review_report": "questions_supervisor_agent"},
        )
        workflow.add_conditional_edges(
            "detections_agent",
            real_time_router,
            {"call_tool": "detections_search_tools", "review_report": "questions_supervisor_agent"},
        )
        workflow.add_edge("historical_search_tools", "historical_agent")
        workflow.add_edge("real_time_search_tools", "real_time_agent")
        workflow.add_edge("detections_search_tools", "detections_agent")
        
        workflow.add_edge("ask_human", "ask_human_response")
        workflow.add_edge("ask_human_response", "questions_supervisor_agent")       

        interrupt_after=["ask_human"]

        return workflow.compile(checkpointer=checkpointer,interrupt_after=interrupt_after)
    

    def create_default_state(self) -> BaseState:
        return {
            "name": "questions_graph",
            "messages": [],
            "chat_model": "",
        }

    @property
    def name(self) -> str:
        return "questions_graph"