from dotenv import load_dotenv
from typing import Optional, List
from langchain_core.language_models.chat_models import BaseChatModel
import boto3
from langchain_aws import ChatBedrock
from botocore.config import Config

load_dotenv()

def list_anthropic_models() -> List[str]:
    """
    List all available Anthropic models
    """
    # if os.getenv("ANTHROPIC_API_KEY"):
    #     return ["claude-3-5-sonnet-20240620"]
    # else:
    return ["anthropic.claude-3-5-sonnet-20240620-v1:0"]


def list_available_llm() -> List[str]:
    """
    List all available models
    """
    return list_anthropic_models()

def create_llm_model() -> ChatBedrock:

    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-west-2",
        config=Config(
            read_timeout=300
        ),
        #verify=False
    )
    llm = ChatBedrock(
        model_id=list_anthropic_models()[0],
        model_kwargs=dict(temperature=0, max_tokens=4096),
        client=bedrock_client
    )
    # llm = ChatAnthropic(
    #     model="claude-3-5-sonnet-20240620",
    #     temperature=0,
    #     max_tokens=4096,
    #     timeout=None,
    #     max_retries=2,
    #     # other params...
    # )

    return llm

llm: ChatBedrock = create_llm_model()


def generate_headline(threat):

    messages = [
    (
        "system",
        "You are a SOC(Security Operations Center) assistant.",
    ),
    ("human", f"Given below security event, generate only 1 line headline with Key 'Headline:' suitable for a security operations analyst.\n\n<events>\n\n{threat}\n\n</events>\n"),
    ]
    llm_:ChatBedrock = llm
    output = llm_.invoke(messages)
    return output.content.split('Headline:')[1]


