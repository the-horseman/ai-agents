from .agents import create_tool_agent, create_llm_agent
from pydantic import BaseModel
from typing import Optional
from ..llm.bedrock import llm
from .agents import Agent,create_agent
import uuid
class RemediationResponse(BaseModel):
    content: str
    further_analysis_required: str
    tool_calls: list | str = []


# Simulate Human Approval Step
def human_approval(state):

    approval = f"""If you are happy with above investigation please approve else you can ask more questions. \n
                Approve remediation? (yes/no): """

    state["remediation_suggested"] = state["messages"][-1].content

    return {'content':f"{approval}"}

human_approval_agent = create_agent(human_approval)

def human_approval_response(state):

    approval = state["messages"][-1].content

    print(f"Approval : {approval}")
    
    user_input =  "approved" if approval.strip().lower() == "approved" else f"further_investigation_needed : USER Input - {approval}"

    return {'content':f"{uuid.uuid4()}\n{user_input}",'user_approval':user_input}

human_approval_response_agent = create_agent(human_approval_response)


def remediation_responder(state):
    rem = ''
    if 'remediation_suggested' in state:
        rem = state["remediation_suggested"]
    return {'content':f'{uuid.uuid4()}\n..............\nResponded! \n {rem} \n..............'}


remediation_responder_agent = create_agent(remediation_responder)     

remediation_planner_agent = create_llm_agent(
    llm=llm, schema=RemediationResponse,
    system_message="""
    You are a Senior SOC Remediation planner Agent.
    From the given Threat Insights and Threat investigation details come up with the recommended Remediation action in markdown format.
    """
)