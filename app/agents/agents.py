from pydantic import BaseModel
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def create_tool_agent(llm: ChatBedrock, tools: list, system_message: str):
    """Create an Agent which has access to tools"""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are a helpful AI assistant, collaborating with other assistants.\n"
                " Use the provided tools to progress towards answering the question. Perform only the task mentioned below\n"
                " If you are unable to fully answer, that's OK, another assistant with different tools.\n"
                " Execute what you can to make progress.\n"
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)

def create_llm_agent(llm: ChatBedrock, schema: BaseModel, system_message: str):
    """Create an Agent without tools access"""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " {system_message} "
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    prompt = prompt.partial(system_message=system_message)
    return prompt | llm.with_structured_output(schema=schema)

from abc import ABC

class ResultWrapper:
    def __init__(self, result):
        self.result = result
        # Check if 'content' key is present in the dictionary
        if "content" not in self.result:
            raise KeyError("'content' key is missing from the result dictionary.")


    def dict(self, exclude=None):
        # Convert exclude to a set if it's not None
        if exclude is None:
            exclude = set()
        elif not isinstance(exclude, set):
            raise TypeError("Exclude parameter must be a set.")

        # Use dictionary comprehension to filter out excluded keys
        return {key: value for key, value in self.result.items() if key not in exclude}

class Agent(ABC):
    def __init__(self, func):
        self.func = func  # Store the function that will define the invoke behavior

    def invoke(self, *args, **kwargs):
        # Call the dynamic function stored in self.func
        result = self.func(*args, **kwargs)
         # Ensure the result is a dictionary
        if not isinstance(result, dict):
            raise TypeError("The result of invoke must be a dictionary.")
        
        return ResultWrapper(result)  # Wrap the result

def create_agent(func):
    return Agent(func)  