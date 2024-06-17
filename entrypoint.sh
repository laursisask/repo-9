#!/bin/sh

echo "Creating admin policy"
echo '[{"Description":"Admin policy","Module":"*","Effect":"Allow","Resources":["*"]}]' > admin_policy.json
./modular.py policy add --policy admin_policy --policy_path admin_policy.json
echo "Creating admin group"
./modular.py group add --group admin_group --policy admin_policy

echo "Creating admin user"
if [ -z "$MODULAR_API_INIT_PASSWORD" ]; then
  ./modular.py user add --username "${MODULAR_API_INIT_USERNAME:-admin}" --group admin_group
else
  ./modular.py user add --username "${MODULAR_API_INIT_USERNAME:-admin}" --group admin_group --password "$MODULAR_API_INIT_PASSWORD"
fi
./modular.py run --gunicorn
