import pandas as pd
from confluent_kafka import Producer
import socket
import json
from app.kafka.constants import HOST_IP, KAFKA_PORT, TOPIC

conf = {
    'bootstrap.servers': f'{HOST_IP}:{KAFKA_PORT}',
    'client.id': socket.gethostname()
}

producer = Producer(conf)

detections_file = pd.read_csv(filepath_or_buffer="data/detections-10.csv")

for cur in detections_file.index:
	producer.produce(
        topic=TOPIC,
        key=json.loads(detections_file["EVENT_JSON"][cur])["traceId"], 
        value=detections_file["EVENT_JSON"][cur]
    )

producer.flush()
