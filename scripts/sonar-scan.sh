#!/usr/bin/env bash
# Run the SonarCloud analysis locally through Docker Desktop and print the
# report URL. Any extra args are passed straight to sonar-scanner.
set -euo pipefail
cd "$(dirname "$0")/.."

# SONAR_TOKEN comes from .env (git-ignored) or the environment.
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

if [ -z "${SONAR_TOKEN:-}" ]; then
  echo "SONAR_TOKEN is not set." >&2
  echo "Create one at https://sonarcloud.io/account/security and put it in .env:" >&2
  echo "  echo 'SONAR_TOKEN=your_token_here' >> .env" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running — start Docker Desktop first." >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "→ scanning branch '$BRANCH' via sonar-scanner-cli container…"

SONAR_TOKEN="$SONAR_TOKEN" docker compose -f docker-compose.sonar.yml run --rm scanner \
  -Dsonar.branch.name="$BRANCH" \
  "$@"

PROJECT_KEY="$(grep -E '^sonar.projectKey=' sonar-project.properties | cut -d= -f2)"
echo
echo "→ report: https://sonarcloud.io/project/overview?id=${PROJECT_KEY}&branch=${BRANCH}"
