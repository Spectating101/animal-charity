.PHONY: test smoke verify run seed docker-build

test:
	python -m unittest discover -s tests -v

smoke:
	@db=$$(mktemp /tmp/afrn-smoke-XXXXXX.db); rm -f "$$db"; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python scripts/seed_demo.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); assert c.get('/health').json()['ok']; assert c.get('/v1/summary').status_code == 200"; \
	rm -f "$$db" "$$db-shm" "$$db-wal"

verify: test smoke
	python -m compileall -q app scripts tests

run:
	fastapi dev app/main.py

seed:
	python scripts/seed_demo.py

docker-build:
	docker build -t animal-feed-relief-network:local .
