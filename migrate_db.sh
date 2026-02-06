#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Activate env and run migration
echo "⚙️  Running Database Migration..."
./env/bin/python manage_db.py

echo "✅ Migration Complete."