#!/bin/bash

read -p "Enter DB name: " DB_NAME
read -p "Enter DB username: " DB_USER
read -sp "Enter DB password: " DB_PASSWORD
echo

cat <<EOF > ./../.env
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EOF

echo ".env file created."