from langgraph.graph import StateGraph, END
from .base import BaseWorkflow
from functools import partial
from langgraph.graph import StateGraph, START, END
from ..agents.remediation import remediation_planner_agent, human_approval_agent, remediation_responder_agent,human_approval_response_agent
from ..router.routers import human_approval_router
from ..checkpoint.postgres_saver import HumanApprovalPostgresSaver
from langgraph.graph import END, START
from .base import BaseState


class RemiadiationPlannerWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def create_graph(self, checkpointer : HumanApprovalPostgresSaver) -> StateGraph:
  
        workflow = StateGraph(BaseState)
        workflow.add_edge(START,"remediation_planner_node")    

        remiadiation_planner_node = partial(super().agent_node, agent=remediation_planner_agent, name="remediation_planner_agent")
        workflow.add_node("remediation_planner_node",remiadiation_planner_node)

        workflow.add_edge("remediation_planner_node","human_approval")

        human_approval_node = partial(super().agent_node, agent=human_approval_agent, name="human_approval")
        workflow.add_node("human_approval",human_approval_node)

        human_approval_response_node = partial(super().agent_node, agent=human_approval_response_agent, name="human_approval_response_node")
        workflow.add_node("human_approval_response",human_approval_response_node)

        workflow.add_edge("human_approval","human_approval_response")

        interrupt_after=["human_approval"]

        return workflow.compile(checkpointer=checkpointer,interrupt_after=interrupt_after)
    

    def create_default_state(self) -> BaseState:
        return {
            "name": "remediation_planner_graph",
            "messages": [],
            "chat_model": "",
        }

    @property
    def name(self) -> str:
        return "remediation_planner_graph"