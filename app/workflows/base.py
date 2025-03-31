import operator
from abc import ABC, abstractmethod
from typing import Annotated, Any, Dict, Sequence, TypedDict

from langchain_core.messages import (AIMessage, AnyMessage,HumanMessage, ToolMessage)
from langgraph.graph import StateGraph

class BaseWorkflow(ABC):
    @abstractmethod
    def create_graph(self) -> StateGraph:
        """
        Define the state graph of the workflow.
        """
        pass

    @abstractmethod
    def create_default_state(self) -> Dict[str, Any]:
        """
        Define the default state of the workflow.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    def agent_node(self, state, agent, name):
        result = agent.invoke(state)
        # We convert the agent output into a format that is suitable to append to the global state
        tool_calls = getattr(result, "tool_calls", None)
        if isinstance(result, ToolMessage):
            pass
        elif tool_calls:
            result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        # elif "supervisor_agent" in name :
        #     # Implementing a Soft Stop
        #     if len(state["messages"]) > 100:
        #         result.further_analysis_required = "none"

        #     if result.further_analysis_required.lower() == 'none':
        #         result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        #     else:
        #         result.content = f'Use the tools given to you and try to answer the leads that are shared to you. the leads are - {str(result.lead)}'
        #         result = HumanMessage(**result.dict(exclude={"type", "name", "lead", "unsolved_leads"}), name=name)
        else:
            result = HumanMessage(**result.dict(exclude={"type", "name"}), name=name)
        return {
            "messages": [result],
            "sender": name,
        }

class BaseState(TypedDict):
    # Message history
    messages: Annotated[Sequence[AnyMessage], operator.add]
    sender: str