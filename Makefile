.PHONY: test smoke landscape-smoke verify run seed docker-build

test:
	python -m unittest discover -s tests -v

smoke:
	@db=$$(mktemp /tmp/afrn-smoke-XXXXXX.db); rm -f "$$db"; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python scripts/seed_demo.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); assert c.get('/health').json()['ok']; assert c.get('/v1/summary').status_code == 200"; \
	rm -f "$$db" "$$db-shm" "$$db-wal"

landscape-smoke:
	@python scripts/scan_landscape.py examples/taoyuan_public_baseline.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['cases']==[]; assert d['data_gaps']"
	@python scripts/scan_landscape.py examples/taoyuan_synthetic_incident.json | python -c "import json,sys; d=json.load(sys.stdin); c=d['cases'][0]; assert c['bottleneck']=='last_mile_logistics'; assert c['actuator']=='logistics.dispatch_request'"

verify: test smoke landscape-smoke
	python -m compileall -q app scripts tests

run:
	fastapi dev app/main.py

seed:
	python scripts/seed_demo.py

docker-build:
	docker build -t animal-feed-relief-network:local .
