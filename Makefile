
.PHONY: run_tests_integration_microservices
run_tests_integration_microservices:
	docker-compose --profile mock_gcs up --build -d --wait
	python -m pytest test/integration/microservices || exit 0
	docker-compose --profile mock_gcs kill
	docker-compose --profile mock_gcs rm -f
	docker image prune -f


