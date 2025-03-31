import logging
import os
import logging,os,uuid
import logging.config
import yaml
from app.utils.prompts import *
import json
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import json
from app.utils.transform import transform_traces
from app.checkpoint.postgres_saver import HumanApprovalPostgresSaver,HumanInputType
from app.graph import create_graph
from app.utils.constants import DB_URI
from app.llm.bedrock import generate_headline

load_dotenv()

os.environ['SSL_CERT_FILE']="./proxy.crt"
os.environ['REQUESTS_CA_BUNDLE']="./proxy.crt"

with open('logging.yaml', 'r') as f:
    logging_config = yaml.safe_load(f)

log_level = os.getenv('LOG_LEVEL', logging_config['loggers']['lightweight-investigation']['level'])
logging_config['loggers']['lightweight-investigation']['level'] = log_level

# Get logging level from environment variable, default to INFO if not set
numeric_level = getattr(logging, log_level, None)

logging.config.dictConfig(logging_config)
logger = logging.getLogger('lightweight-investigation')
logger.setLevel(numeric_level)
logger.info(f"Logging level set to: {log_level} {numeric_level}")

GRAPH_RECURSION_LIMIT = 200


################## DB checkpoint ##########################

from psycopg_pool import ConnectionPool

with ConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
) as pool:
    checkpointer = HumanApprovalPostgresSaver(pool)

    # NOTE: you need to call .setup() the first time you're using your checkpointer
    checkpointer.setup()
    ################### Graph #########################

    graph = create_graph(checkpointer)
    
    logger.info(f"Graph created.....{graph}")

    ################### Runner #########################
    path = './data/payloads/monitoring'
    payloads = sorted(os.listdir(path=path))

    for i in payloads:    
        if "preprod_" not in i:
            continue
        print(f"\n\n{'*'*25}\t\t STARTING FOR \t\t {i} \t\t {'*'*25}\n\n")

        with open(f"{path}/{i}", "r+") as f:
            threat = json.load(f)
            threat["id"] = threat["detections"][0]["id"]
            threat["severity"] = threat["detections"][0]["severity"]
            threat["iocs"] = transform_traces(threat["traces"])
            threat.pop("traces")
        try:
            input = {
                    "messages": [
                        HumanMessage(
                            content=f" <events>\n\n{json.dumps(threat,indent=1)}\n\n</events>\n"
                        )
                    ],
                }
            headline = generate_headline(threat)    
            print(f"Headline for {threat["id"]} : {headline}")
            interrupt_after=["human_approval","ask_human"]
            thread_id = f"{str(threat["id"])}-{str(uuid.uuid4())}"
            config= {"configurable": {"thread_id": thread_id},"recursion_limit": GRAPH_RECURSION_LIMIT}
            for namespace,chunk in graph.stream( input,
                                    stream_mode="updates",
                                    config= config,
                                    subgraphs=True):
                for node, event in chunk.items():
                    print(f"Receiving update from namespace : {namespace}, node: '{node}'")
                    if "messages" in event:
                        logger.info(f"\n\n{event["messages"][-1].pretty_repr()}\n\n") 
                        if event["messages"][-1].name and event["messages"][-1].name in interrupt_after:
                            # Create approval request
                            # Get the latest checkpoint for this thread
                            state = graph.get_state(config, subgraphs=True)
                            cfg = state.tasks[0].state.config
                            print(f"State config {cfg}") 

                            checkpointer.create_input_request(
                                config=cfg,
                                input_type=HumanInputType.APPROVAL if event["messages"][-1].name == "human_approval" else HumanInputType.QUESTION,
                                question=event["messages"][-1].content,
                                metadata={
                                    "threat_id":str(threat["id"]),
                                    "severity":str(threat["severity"]),
                                    "headline": str(headline)
                                    # add threat desc
                                }
                            )
        except Exception as e:
            logger.error(f"SKIPPING because of ",e)


    

