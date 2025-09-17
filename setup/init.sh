#!/bin/bash

#pip install -r requirements.txt

# 1. Create .env file
# ./createdotenv.sh

# 2. Make sure connectdb.sh is executable
chmod +x connectdb.sh

# 3. Run setup SQL and dummy data on the chosen DB
./connectdb.sh < setup.sql
# ./connectdb.sh < dummy_data.sql