from langgraph.graph import StateGraph, END
from .base import BaseWorkflow
from functools import partial
from langgraph.graph import StateGraph, START, END
from ..agents.remediation import remediation_planner_agent, human_approval_agent, remediation_responder_agent,human_approval_response_agent
from ..router.routers import human_approval_router
from ..checkpoint.postgres_saver import HumanApprovalPostgresSaver
from langgraph.graph import END, START
from .base import BaseState


class RemiadiationResponderWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def create_graph(self, checkpointer : HumanApprovalPostgresSaver) -> StateGraph:
  
        workflow = StateGraph(BaseState)
        workflow.add_edge(START,"remediation_responder_node")    

        remediation_responder_node = partial(super().agent_node, agent=remediation_responder_agent, name="remediation_responder_agent")
        workflow.add_node("remediation_responder_node",remediation_responder_node)

        workflow.add_edge("remediation_responder_node",END)

        return workflow.compile(checkpointer=checkpointer)
    

    def create_default_state(self) -> BaseState:
        return {
            "name": "remediation_responder_graph",
            "messages": [],
            "chat_model": "",
        }

    @property
    def name(self) -> str:
        return "remediation_responder_graph"