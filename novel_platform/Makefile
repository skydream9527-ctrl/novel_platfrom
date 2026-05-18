.PHONY: install dev backend frontend prod prod-build prod-run clean

install: backend-install frontend-install

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

frontend-install:
	cd frontend && npm install

dev:
	@echo "Starting dev servers..."
	@cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000 &
	@cd frontend && npm run dev &
	@wait

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

prod: prod-build prod-run

prod-build:
	cd frontend && npm run build

prod-run:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist data/

pack:
	@echo "Packing..."
	zip -r novel-platform-$$(date +%Y%m%d).zip \
		.env .env.example .gitignore Makefile deploy.sh README.md \
		backend/ frontend/ \
		--exclude "backend/.venv/*" "frontend/node_modules/*" "data/*" ".cache/*"
