with open('core/db_resources.py', 'r') as f:
    content = f.read()

# Update SELECT in resources_get_all
content = content.replace(
    "COALESCE(view_count, 0) AS view_count,\n            last_viewed_at\n        FROM public_resources",
    "COALESCE(view_count, 0) AS view_count,\n            last_viewed_at,\n            approval_status,\n            sensitivity_classification\n        FROM public_resources"
)

# Update INSERT in resources_create to default to 'PendingApproval'
content = content.replace(
    "INSERT INTO public_resources (page_name, business_name, description, category, url, admin_only, department, added_by)\n        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
    "INSERT INTO public_resources (page_name, business_name, description, category, url, admin_only, department, added_by, approval_status)\n        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PendingApproval')"
)

with open('core/db_resources.py', 'w') as f:
    f.write(content)
