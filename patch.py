import re

with open('apps_metadata.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '\"description\": \"Domain for Traefik Dashboard\",\n                \"required\": True',
    '\"description\": \"Domain for Traefik Dashboard\",\n                \"required\": True,\n                \"auto_generate\": False'
)

content = content.replace(
    '\"description\": \"Email for Let\'s Encrypt certificates\",\n                \"required\": True',
    '\"description\": \"Email for Let\'s Encrypt certificates\",\n                \"required\": True,\n                \"auto_generate\": False'
)

content = content.replace(
    '\"description\": \"Email for TLS certificates\",\n                \"required\": True',
    '\"description\": \"Email for TLS certificates\",\n                \"required\": True,\n                \"auto_generate\": False'
)

with open('apps_metadata.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully!')
