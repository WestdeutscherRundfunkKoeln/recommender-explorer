
.PHONY: run_tests_integration_microservices
run_tests_integration_microservices:
	docker compose up --build -d --wait
	python -m pytest test/integration/microservices -vv || exit 0
	docker compose  kill
	docker compose  rm -f


.PHONY: run_tests_integration_controller
run_tests_integration_controller:
	docker compose up --build -d --wait
	python -m pytest --config=config/config_testing.yaml test/integration/test_controller_integrations.py || exit 0
	docker compose  kill
	docker compose  rm -f

