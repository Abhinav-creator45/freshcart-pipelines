"""Usage: python -m stream.driver NAME PATTERN."""
import os,sys,json,signal
import pika
URL=os.environ.get('RABBITMQ_URL','amqp://guest:guest@127.0.0.1:5673/%2F')
def main(name,pattern):
    connection=pika.BlockingConnection(pika.URLParameters(URL));ch=connection.channel()
    ch.exchange_declare(exchange='rapido-dispatch',exchange_type='topic')
    queue=ch.queue_declare(queue='',exclusive=True).method.queue
    ch.queue_bind(exchange='rapido-dispatch',queue=queue,routing_key=pattern)
    print('READY',name,pattern,flush=True)
    def receive(channel,method,properties,body):
        data=json.loads(body)
        if 'zone' not in data:
            channel.basic_nack(delivery_tag=method.delivery_tag,requeue=False)
            print('DISCARD',name,data.get('id'),method.routing_key,'requeue=False',flush=True)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print('ACK',name,data['id'],method.routing_key,flush=True)
    ch.basic_consume(queue=queue,on_message_callback=receive,auto_ack=False)
    def stop(*args):ch.stop_consuming()
    signal.signal(signal.SIGTERM,stop)
    try:ch.start_consuming()
    finally:
        if connection.is_open:connection.close()
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
