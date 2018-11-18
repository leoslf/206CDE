TARGET=TowngasBilling
VENV_DIR=venv
BIN=$(VENV_DIR)/bin
PIP_REQUIREMENTS=requirements.txt
SET_PYTHONPATH = PYTHONPATH=$(VENV_DIR);
VENV_INIT = @$(SET_PYTHONPATH); source $(BIN)/activate

all: venv

venv: venv_init $(BIN)/activate deps

venv_init: directory_structure
	@test -d $(VENV_DIR) || virtualenv $(VENV_DIR)

directory_structure: $(TARGET)/ docs/ tests/

%/:
	mkdir -p $@

deps:
	pip install -Ur $(PIP_REQUIREMENTS)

freeze: venv
	pip freeze > $(PIP_REQUIREMENTS)
	
devbuild: venv setup.py
	@python setup.py install

test: tests
	@py.test tests

clean_venv: $(VENV_DIR)
	$(RM) $(VENV_DIR)

.PHONY: venv test
