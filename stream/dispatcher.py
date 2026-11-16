"""Publish one request every two seconds; every tenth request lacks zone."""
import os,json,time,random,uuid
from datetime import datetime,timezone
import pika
URL=os.environ.get('RABBITMQ_URL','amqp://guest:guest@127.0.0.1:5673/%2F')
def main():
    connection=pika.BlockingConnection(pika.URLParameters(URL))
    ch=connection.channel();ch.exchange_declare(exchange='rapido-dispatch',exchange_type='topic')
    ch.confirm_delivery()
    probes=[('probe-food','bangalore.koramangala.food',{'city':'bangalore','zone':'koramangala','type':'food'}),('probe-drop','chennai.whitefield.ride',{'city':'chennai','zone':'whitefield','type':'ride'}),('probe-short','bangalore.koramangala',{'city':'bangalore','zone':'koramangala','type':'food'})]
    for identifier,key,data in probes:
        data.update(id=identifier,ts=datetime.now(timezone.utc).isoformat())
        try:ch.basic_publish(exchange='rapido-dispatch',routing_key=key,body=json.dumps(data),mandatory=True);print('PROBE',identifier,key,flush=True)
        except pika.exceptions.UnroutableError:print('DROPPED',identifier,key,flush=True)
    rng=random.Random(6);start=time.monotonic()
    for i in range(1,61):
        city=rng.choice(['bangalore','chennai'])
        zone=rng.choice(['koramangala','indiranagar','whitefield'] if city=='bangalore' else ['tnagar','adyar'])
        kind=rng.choice(['food','ride'])
        if i%10==0:city,zone,kind='bangalore','koramangala','food'
        key=f'{city}.{zone}.{kind}'
        data={'id':f'order-{i:03d}','city':city,'zone':zone,'type':kind,'ts':datetime.now(timezone.utc).isoformat()}
        if i%10==0:del data['zone']
        ch.basic_publish(exchange='rapido-dispatch',routing_key=key,body=json.dumps(data))
        print('SENT',data['id'],key,'BAD' if i%10==0 else 'GOOD',flush=True)
        time.sleep(max(0,start+2*i-time.monotonic()))
    print('FINISHED',60,'messages',round(time.monotonic()-start,3),'seconds',flush=True)
    connection.close()
if __name__=='__main__':main()
