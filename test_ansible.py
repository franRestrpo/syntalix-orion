import subprocess
open('test.yml', 'w').write('''
- hosts: localhost
  gather_facts: no
  tasks:
    - debug:
        msg: "Val: {{ MY_VAR | default('fallback', true) }}"
''')
open('vars.json', 'w').write('{"MY_VAR": "None"}')
try:
    out = subprocess.check_output(['.venv/Scripts/python.exe', '-m', 'ansible', 'playbook', 'test.yml', '-e', '@vars.json'])
    print(out.decode())
except Exception as e:
    print(e)
