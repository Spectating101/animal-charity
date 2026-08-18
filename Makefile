.PHONY: test verify run seed docker-build

test:
	python -m unittest discover -s tests -v

verify: test
	python -m compileall -q app scripts tests

run:
	fastapi dev app/main.py

seed:
	python scripts/seed_demo.py

docker-build:
	docker build -t animal-feed-relief-network:local .
