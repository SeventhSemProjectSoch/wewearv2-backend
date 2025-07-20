# Makefile for wewearv2-backend

# Variables
PYTHON=python3
MANAGE=$(PYTHON) manage.py

.PHONY: migrate migrate-revert migrate-reset run list-makeless-command help

# Help command to list available commands
help:
	@echo "Available commands:"
	@echo "  migrate             Apply migrations"
	@echo "  migrate-revert      Revert last N migrations (num=N required)"
	@echo "  migrate-reset       Reset last N migrations (num=N required)"
	@echo "  run                 Run development server"
	@echo "  list-makeless-command  Commands to run without make installed"

# Apply migrations
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

# Revert last {num} migrations
# Usage: make migrate-revert num=1
migrate-revert:
ifndef num
	$(error Please specify num, e.g. make migrate-revert num=1)
endif
	@echo "Reverting last $(num) migrations"
	$(MANAGE) migrate --fake $(shell $(MANAGE) showmigrations | grep "\[X\]" | tail -n $(num) | awk '{print $$1}') zero

# Reset last {num} migrations (revert then re-apply)
# Usage: make migrate-reset num=1
migrate-reset:
ifndef num
	$(error Please specify num, e.g. make migrate-reset num=1)
endif
	@echo "Resetting last $(num) migrations"
	$(MAKE) migrate-revert num=$(num)
	$(MAKE) migrate

# Run development server
run:
	$(MANAGE) runserver 0.0.0.0:8000

# List commands for users without make installed
list-makeless-command:
	@echo "Run these commands manually:"
	@echo "1. cd backend"
	@echo "2.1. python3 manage.py makemigrations"
	@echo "2.2. python3 manage.py migrate"
	@echo "3. python3 manage.py runserver 0.0.0.0:8000"

