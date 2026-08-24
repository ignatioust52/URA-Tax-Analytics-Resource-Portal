from core.db_resources import resources_get_all
from backend.api.resources import filter_resources_by_rbac
import pprint

# Mock session for a non-admin user
# Let's say user_id=2 (assuming 1 is admin)
session = {
    "id": 2,
    "active_department_id": 1,
    "role": "user"
}

records = resources_get_all()
# filter for just one 'EVERYONE' resource to trace
filtered = filter_resources_by_rbac(records, session)
for r in filtered:
    print(r["business_name"], r["visibility"], r.get("approval_status"))
