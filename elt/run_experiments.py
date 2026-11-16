"""Run B1–B5 on the student's own Snowflake trial; no credentials are saved."""
import json,contextlib,io
from pathlib import Path
from elt import freshcart as f
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'; E.mkdir(exist_ok=True)
results={}
def capture(label,fn):
    out=io.StringIO()
    with contextlib.redirect_stdout(out): value=fn()
    log=out.getvalue(); print(log,flush=True)
    (E/(label+'.txt')).write_text(log)
    results[label]=value
    (E/'freshcart-results.json').write_text(json.dumps(results,indent=2,default=str))
    return value

def totals(): return f.query('SELECT COUNT(*), SUM(amount_inr), SUM(loyalty_points) FROM gold.fct_orders')[0]
def stamp(): return dict(f.query('SELECT order_id,published_at FROM gold.fct_orders'))
def baseline():
    original=f.SQL_10_ORDERS_CLEAN; f.SQL_10_ORDERS_CLEAN=f.SQL_10_BASELINE
    f.run_sql(f.SQL_00_SETUP); f.run_pipeline()
    counts={name:f.query('SELECT COUNT(*) FROM '+name)[0][0] for name in ['bronze.orders_raw','silver.orders_clean','quarantine.orders','silver.orders_dedup']}
    print('B1 counts',counts);print('Gold',totals())
    assert list(counts.values())==[8,6,2,4] and tuple(map(float,totals()))==(4,7785,126)
    f.SQL_10_ORDERS_CLEAN=original
    return {'counts':counts,'gold':totals()}
def trace():
    raw=f.query("SELECT source,raw FROM bronze.orders_raw WHERE COALESCE(raw:order_id::STRING,raw:orderId::STRING)='ORD-1003' ORDER BY source")
    gold=f.query("SELECT * FROM gold.fct_orders WHERE order_id IN ('ORD-1001','ORD-1003','ORD-1005') ORDER BY order_id")
    print('B2 raw',raw);print('B2 gold',gold)
    return {'raw':raw,'gold':gold}
def validation():
    before=f.query("SELECT source,reasons FROM silver.orders_checked WHERE order_id='ORD-1006'")
    f.run_pipeline()
    after=f.query("SELECT DISTINCT source,reasons FROM silver.orders_checked WHERE order_id='ORD-1006'")
    q=f.query("SELECT COUNT(*) FROM quarantine.orders WHERE order_id='ORD-1006'")[0][0]
    print('BEFORE',before);print('AFTER',after);print('Quarantine rows',q);print('Gold',totals())
    assert q==1 and tuple(map(float,totals()))==(4,7785,126)
    return {'before':before,'after':after,'quarantine_rows':q,'gold':totals()}
def history():
    print('PRE-RUN EXPECTATIONS (committed before experiments):', (ROOT/'predictions.json').read_text())
    previous=stamp()
    f.MOCK_CRM_TIER_EVENTS.append({'cust_id':'CUST-02','email':'arjun.k@yahoo.in','tier':'Gold','effective_from':'2026-08-15'})
    f.run_pipeline()
    rows=f.query("SELECT * FROM dim.customers_scd2 WHERE cust_id='CUST-02' ORDER BY valid_from")
    order=f.query("SELECT tier,loyalty_points FROM gold.fct_orders WHERE order_id='ORD-1002'")[0]
    changed=sum(previous[k]!=v for k,v in stamp().items())
    print('SCD2',rows);print('ORD-1002',order);print('Gold',totals());print('Changed published_at',changed)
    assert len(rows)==2 and order==('Gold',70) and float(totals()[2])==161 and changed==1
    prior=stamp(); bronze=f.query('SELECT COUNT(*) FROM bronze.orders_raw')[0][0]
    f.run_pipeline(); growth=f.query('SELECT COUNT(*) FROM bronze.orders_raw')[0][0]-bronze
    changed_again=sum(prior[k]!=v for k,v in stamp().items())
    print('IDENTICAL RE-RUN bronze growth',growth,'published_at changed',changed_again)
    assert growth==8 and changed_again==0
    return {'history':rows,'order':order,'gold':totals(),'changed':changed,'rerun_bronze_growth':growth,'rerun_published_changed':changed_again}
def quality():
    injected={'order_id':'ORD-FX-TEST','cust_email':'arjun.k@yahoo.in','cust_name':'Arjun K','order_date':'2026-12-31','amount':'100','currency':'USD','pincode':'560034','updated_at':'2026-12-31 10:00:00'}
    f.MOCK_WEB_ORDERS.append(injected);f.run_pipeline()
    fail=f.query('SELECT COUNT(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND amount_inr IS NULL')[0][0]
    print('B5 deliberate failing check:',fail,'PROBLEM');assert fail==1
    f.MOCK_WEB_ORDERS.remove(injected)
    # Only remove this named disposable mock record, including append-only input history.
    f.query("DELETE FROM bronze.orders_raw WHERE raw:order_id::STRING='ORD-FX-TEST'")
    f.query("DELETE FROM gold.fct_orders WHERE order_id='ORD-FX-TEST'")
    f.run_pipeline(); final=f.query('SELECT COUNT(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND amount_inr IS NULL')[0][0]
    print('B5 restored:',final,'OK');assert final==0
    return {'failing_value':fail,'restored_value':final,'final_gold':totals()}
if __name__=='__main__':
    f.connect()
    try:
        for label,fn in [('B1-baseline',baseline),('B2-trace',trace),('B3-currency',validation),('B4-history',history),('B5-quality',quality)]:capture(label,fn)
    finally:
        f.query('ALTER WAREHOUSE FRESHCART_WH SUSPEND');f.conn.close()
