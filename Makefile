COMPOSE = docker compose

.PHONY: up down logs ps migrate test-api smoke release

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) exec api sh -c "cd /app/apps/api && alembic -c alembic.ini upgrade head"

test-api:
	$(COMPOSE) run --rm api sh -c "cd /app/apps/api && pip install --no-cache-dir -r requirements-dev.txt && pytest -q"

smoke:
	$(COMPOSE) exec api sh -c "python -c \"import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health', timeout=5).read().decode())\""

release:
	@test -n "$(VERSION)" || (echo "Use: make release VERSION=x.y.z" && exit 1)
	./release.sh $(VERSION)
