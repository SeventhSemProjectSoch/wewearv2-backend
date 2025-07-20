PYTHON=python3
MANAGE=$(PYTHON) manage.py

.PHONY: migrate migrate-revert migrate-reset run list-makeless-command help

help:
	@echo "Available commands:"
	@echo "  migrate | mg                       Apply migrations"
	@echo "  migrate-revert | mg_rv             Revert last N migrations (num=N required)"
	@echo "  migrate-reset | mg_rst             Reset last N migrations (num=N required)"
	@echo "  run | r                            Run development server"
	@echo "  list-makeless-command | lmc        Commands to run without make installed"

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

mg:migrate

migrate-revert:
ifndef num
	$(error Please specify num, e.g. make migrate-revert num=1)
endif
	@echo "Reverting last $(num) migrations"
	$(MANAGE) migrate --fake $(shell $(MANAGE) showmigrations | grep "\[X\]" | tail -n $(num) | awk '{print $$1}') zero

mg_rv:migrate-revert

migrate-reset:
ifndef num
	$(error Please specify num, e.g. make migrate-reset num=1)
endif
	@echo "Resetting last $(num) migrations"
	$(MAKE) migrate-revert num=$(num)
	$(MAKE) migrate

mg_rst:migrate-reset

run:
	$(MANAGE) runserver 0.0.0.0:8000

r:run

list-makeless-command:
	@echo "Run these commands manually:"
	@echo "1. cd backend"
	@echo "2.1. python3 manage.py makemigrations"
	@echo "2.2. python3 manage.py migrate"
	@echo "3. python3 manage.py runserver 0.0.0.0:8000"


lmc:list-makeless-command