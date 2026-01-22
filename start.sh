#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting RAG application...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for PostgreSQL database...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h "${DATABASE_HOST:-localhost}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}" 2>/dev/null; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo -e "${YELLOW}Waiting... (attempt $attempt/$max_attempts)${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ Database failed to respond after $max_attempts attempts${NC}"
    echo "Continuing anyway - database might be available soon..."
fi

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
if alembic upgrade head; then
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${RED}✗ Migrations failed - continuing anyway${NC}"
fi

# Start the application
echo -e "${YELLOW}Starting Uvicorn server...${NC}"
exec uvicorn rag.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1
