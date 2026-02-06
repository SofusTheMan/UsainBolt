#!/bin/bash

#pip install -r requirements.txt

# 1. Create .env file
# ./setup/createdotenv.sh

# 2. Make sure connectdb.sh is executable
# chmod +x setup/connectdb.sh

# 3. Run setup SQL and dummy data on the chosen DB
# ./setup/connectdb.sh < ./setup/setup.sql
# ./connectdb.sh < dummy_data.sql

psql "$DATABASE_URL" -f setup.sql


