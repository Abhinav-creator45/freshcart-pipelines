# From Git to Gold — Abhinav Harsh, 23BCS006

CS-8037 Data Engineering. This repository contains the mandatory coursework components. The optional stream-to-lakehouse bonus is not attempted.

## Files for evaluation

- **Report PDF:** `23BCS006_Abhinav_Harsh_Pipelines.pdf`, provided as a PDF attachment in Google Classroom.
- **FreshCart ELT:** `elt/freshcart.py` and `elt/run_experiments.py`; the notebook with real outputs is `elt/FreshCart_Pipeline.ipynb`.
- **Mage project and executed notebook:** `iris_project/` and `iris_project/Iris_Pipeline.ipynb`.
- **RabbitMQ:** `stream/dispatcher.py`, `stream/driver.py`, and the repeatable `stream/run_lab.py`.
- **Predictions:** `predictions.json`, recorded in the initial commit before the experiments.
- **Actual run logs:** `evidence/`.

**Verified evidence:** passing/failing CI and fix, five Mage depth experiments, the real Cloudflare graph, the two-minute RabbitMQ run, and all five live Snowflake experiments.

**Account requirement exception:** New-account signup failed with both email addresses and the Google route. With the owner’s permission, fresh experiments ran in `FRESHCART23BCS006` and `ABHINAV_LAB_WH` on a provided existing trial. This differs from the assignment’s own-account requirement; the report discloses it. The screenshots show the actual results without altering the account identity or numbers.

The live FreshCart notebook ran inside Snowflake Workspaces using an authenticated Snowpark session. Snowpark PUT uploaded each raw file; COPY and transformation SQL retained the course logic. Because the native Workspace download omits stored outputs, the exported notebook restores its captured real stdout and result bundle for review.

## Reproduce

Use Python 3.12 in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m pytest -q
mage run iris_project iris_classifier --test
python iris_project/depth_experiment.py
```

The CI deliberately failed at `1792fc7` with `test_size=0.3`, and passed after the fix at `d61302a` restored `test_size=0.2`. The actual Actions run screenshots are prepared for the report appendix.

For the local FreshCart CLI, use a fresh authorized namespace and set the non-secret account identifier and username through `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_USER`. Run `python -m elt.run_experiments`; it asks for the password through a hidden prompt. The baseline expects a clean sample database. Each subsequent extraction appends eight raw orders; gold is deduplicated and merged by order ID. B5 removes only its named synthetic `ORD-FX-TEST` order after proving the new check fails.

For the live Snowflake notebook, import it into Snowflake Workspaces and connect an authorized notebook service. It uses `get_active_session()` and the included `snowpark_adapter.py`; no password or token is embedded. Baseline counts require an empty assignment database. The report and saved outputs cover the original first run and subsequent history/quality experiments.

For the local stream experiment:

```sh
docker run -d --name abhinav-assignment-rabbitmq -p 127.0.0.1:5673:5672 rabbitmq:4-alpine
# Wait for the broker to be ready, then:
python -m stream.run_lab
docker stop abhinav-assignment-rabbitmq
```

The default `guest:guest` broker URL is only a local development credential on loopback port 5673. Set `RABBITMQ_URL` privately for another broker. Never commit a hosted broker URL or password.

The actual two-minute run used Ravi, Meena and Control. It sent 60 timed requests, plus three routing probes. Each running driver discarded six malformed deliveries with `requeue=False`. The six-driver routing table is a paper prediction; only the three named drivers were launched.

## Attribution

The FreshCart sample data/SQL and initial Iris blocks come from the course notebooks. Implementation, pre-run predictions, testing and report preparation were AI-assisted. All included execution evidence comes from this separate assignment. The student should review and understand the code and explanations for the viva. No credentials, generated model files or CSV outputs are committed.
