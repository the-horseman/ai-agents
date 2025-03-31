from functools import partial

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from ..agents.insights import insight_reporting_agent
from ..router.routers import insight_router
from ..tools.insights import insight_tools
from .base import BaseWorkflow
from langgraph.graph import END, START
from ..checkpoint.postgres_saver import HumanApprovalPostgresSaver
from .base import BaseState
class InsightsWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def create_graph(self, checkpointer : HumanApprovalPostgresSaver) -> StateGraph:
        insights_workflow = StateGraph(BaseState)
        
        insight_reporting_node = partial(super().agent_node, agent=insight_reporting_agent, name="insight_reporting_agent")
        get_details_on_IOC_tool_node = ToolNode(insight_tools)

        insights_workflow.add_edge(START,"insight_reporting_agent")
        insights_workflow.add_node("insight_reporting_agent", insight_reporting_node)
        insights_workflow.add_node("get_details_on_IOC_tool_node", get_details_on_IOC_tool_node)

        insights_workflow.add_conditional_edges(
            "insight_reporting_agent",
            insight_router,
            { "__end__": END, "call_tool": "get_details_on_IOC_tool_node"},
        )
        insights_workflow.add_edge("get_details_on_IOC_tool_node", "insight_reporting_agent")

        return insights_workflow.compile(checkpointer=checkpointer)
    
    
    def create_default_state(self) -> BaseState:
        return {
            "name": "insights_graph",
            "messages": [],
            "chat_model": "",
        }
    
    @property
    def name(self) -> str:
        return "insights_graph"


