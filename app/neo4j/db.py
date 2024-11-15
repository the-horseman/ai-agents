from neo4j import GraphDatabase

URI = "neo4j://10.54.1.212:7687"
AUTH = ("neo4j", "secretgraph")

driver = GraphDatabase.driver(uri=URI, auth=AUTH)

def add_detection(detection):
    query = """
    CREATE (p:Process {
    name: $process_name,
    path: $process_path,
    sha256: $process_sha256,
    integrity: $process_integrity,
    embedFilename: $process_embed_file_name
    })

    CREATE (d:Detection {
    ruleId: {detection["ruleId"]},
    severity: {detection["severity"]},
    score: {detection["score"]}
    })

    CREATE (p)-[:DETECTED_BECAUSE]->(d)

    FOREACH (tag IN [{", ".join(detection["detectionTags"])}] |
    MERGE (t:DetectionTag {{name: tag}})
    CREATE (d)-[:HAS_TAG]->(t)
    )

    CREATE (e:Execution {{
    eventDate: datetime({detection["eventDate"]}),
    userDomain: {detection["user"]["domain"]},
    userName: {detection["user"]["name"]},
    hostOs: {detection["h_os"]},
    cmdLine: {detection["cmdLine"]}
    }})

    CREATE (p)-[:HAS_EXECUTION]->(e)
    """
    driver.execute_query(
        query_=query,
        parameters_={
            "process_name": detection["processName"],
            "process_path": detection["processPath"],
            "process_sha256": detection["processSha256"],
            "process_integrity": detection["processIntegrity"],
            "process_embed_file_name": detection["processEmbedFilename"]
        }
    )