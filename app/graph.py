import logging
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from .module_discovery import discover_modules
import logging
import logging.config
from .utils.prompts import *
from .checkpoint.postgres_saver import HumanApprovalPostgresSaver
from .workflows.base import BaseState
from .router.routers import human_approval_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

discovered_workflows = discover_modules()
logger.info(f"Discovered workflows: {list(discovered_workflows.keys())}")


def create_graph(checkpointer : HumanApprovalPostgresSaver) -> CompiledStateGraph:

    logger.info(f"Starting with workflow: insights_graph")
    workflow = StateGraph(BaseState)

    insights_graph =  discovered_workflows["insights_graph"].create_graph(checkpointer)
    workflow.add_node("insights" , insights_graph)
    workflow.add_edge(START, "insights")

    questions_graph = discovered_workflows["questions_graph"].create_graph(checkpointer)
    workflow.add_node("questions" , questions_graph)

    workflow.add_edge("insights", "questions")

    remediation_planner_graph = discovered_workflows["remediation_planner_graph"].create_graph(checkpointer)
    workflow.add_node("remediation_planner" , remediation_planner_graph)

    workflow.add_edge("questions", "remediation_planner")
 
    workflow.add_conditional_edges(
            "remediation_planner",
            human_approval_router,
            {"approved": "remediation_responder", "further_investigation_needed": "questions"},
        )
    remediation_responder_graph = discovered_workflows["remediation_responder_graph"].create_graph(checkpointer)
    workflow.add_node("remediation_responder",remediation_responder_graph)
    workflow.add_edge("remediation_responder",END)

    #interrupt_after=["human_approval","ask_human"]
    
    graph = workflow.compile(checkpointer=checkpointer)
    
    graph.get_graph(xray=1).draw_mermaid_png(output_file_path="workflow.png")

    return graph