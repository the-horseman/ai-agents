from confluent_kafka import Consumer
from app.kafka.constants import HOST_IP, KAFKA_PORT, CONSUMER_GROUP, TOPIC

conf = {
    'bootstrap.servers': f'{HOST_IP}:{KAFKA_PORT}',
    'group.id': CONSUMER_GROUP,
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)

consumer.subscribe([TOPIC])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            # Initial message consumption may take up to
            # `session.timeout.ms` for the consumer group to
            # rebalance and start consuming
            print("Waiting...")
        elif msg.error():
            print("ERROR: %s".format(msg.error()))
        else:
            key = msg.key().decode('utf-8')
            value = msg.value().decode('utf-8')
            # Extract the (optional) key and value, and print.
            print(f"Consumed event from {TOPIC}: \nkey = {key} \nvalue = {value}")
except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()
