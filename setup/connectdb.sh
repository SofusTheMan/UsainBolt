#!/bin/bash

# Load variables from .env
if [ -f ./../.env ]; then
  export $(cat ./.env | xargs)
else
  echo ".env file not found. Run ./createdotenv.sh first."
  exit 1
fi

# Connect using values from .env
psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT"