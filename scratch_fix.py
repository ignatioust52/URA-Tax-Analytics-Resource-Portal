with open("views/public_resources.py", "r") as f:
    lines = f.readlines()

add_start = -1
add_end = -1
edit_start = -1
edit_end = -1

for i, l in enumerate(lines):
    if '# MAIN AREA — "Add New Resource" page' in l:
        add_start = i
    if '# MAIN AREA — "Edit Resource" page' in l:
        add_end = i # just before edit
        edit_start = i
    if '# MAIN AREA — default browse / search / view page (bottom duplicate removed)' in l:
        edit_end = i

print(f"Add: {add_start} to {add_end}")
print(f"Edit: {edit_start} to {edit_end}")

add_block = lines[add_start:add_end]
edit_block = lines[edit_start:edit_end]

# Find the insertion point before the `if resources_df.empty:`
insert_point = -1
for i, l in enumerate(lines):
    if "if resources_df.empty:" in l and i < 250:
        insert_point = i
        break

print(f"Insert at: {insert_point}")

new_lines = lines[:insert_point] + add_block + edit_block + lines[insert_point:add_start] + lines[edit_end:]

with open("views/public_resources.py", "w") as f:
    f.writelines(new_lines)
