PROJECT_NAME ?= $(shell python3 setup.py --name)
PROJECT_VERSION ?= $(shell python3 setup.py --version)

all:
	@echo "make devenv			- Configure dev environment"
	@echo "make sdist			- Build package"
	@echo "make clean			- Remove files created by distutils & dev modules"
	@echo "make test			- Run tests"
	@ehco "make test-env-up 	- Setup docker environment for testing or local development"
	@ehco "make test-env-down 	- Teardown docker environment for testing or local development"
	@exit 0


devenv:
	rm -rf env
	python3.11 -m venv env
	env/bin/pip install -Ue '.[dev]'

clean:
	rm -fr *.egg-info dist

sdist: clean
	env/bin/python setup.py sdist

dist: sdist
	env/bin/pip install -Ue '.'

.PHONY: test-with-env
test-with-env: dist test-env-up test test-env-down

test:
	env/bin/pytest

test-env-up:
	@docker-compose -f build/docker-compose.test.yml up -d

test-env-down:
	@docker-compose -f build/docker-compose.test.yml down -v
