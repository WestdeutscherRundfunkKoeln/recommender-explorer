
.PHONY: run_tests_integration_microservices
run_tests_integration_microservices:
	docker-compose --profile mock_gcs up -d --wait
	python -m pytest test/integration/microservices
	docker-compose --profile mock_gcs kill


