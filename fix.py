with open('site.yml', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

head = content.split('  post_tasks:')[0]

post_tasks = '''  post_tasks:

    - name: "Resumen de Despliegue Completado"
      ansible.builtin.debug:
        msg:
          - "========================================================================"
          - "           SYNTALIX-ORION V2 - DESPLIEGUE COMPLETADO"
          - "========================================================================"
          - " Roles instalados: {{ ansible_enabled_roles | length }}"
          - "========================================================================"

    - name: "Listar servicios desplegados"
      ansible.builtin.debug:
        msg: "{{ ansible_enabled_roles | map('regex_replace', '^', '  * ') | list }}"

    - name: "URLs de Acceso"
      ansible.builtin.debug:
        msg:
          - " URLs de Acceso:"
          - "   - Traefik: https://traefik.{{ lookup('vars', 'TRAEFIK__TRAEFIK_DASHBOARD_URL', default='localhost') }}"
          - "   - Portainer: https://portainer.{{ lookup('vars', 'TRAEFIK__TRAEFIK_DASHBOARD_URL', default='localhost') }}"

    - name: "Comandos utiles post-despliegue"
      ansible.builtin.debug:
        msg:
          - "Comandos utiles:"
          - "  docker stack ls"
          - "  docker service logs <service_name>"

    - name: "Mensaje Final"
      when: "ansible_check_mode | default(false) == false"
      ansible.builtin.debug:
        msg:
          - "========================================================================"
          - "                      ¡DESPLIEGUE EXITOSO!"
          - " "
          - " Syntalix-Orion V2 ha completado la instalacion de los roles seleccionados."
          - " "
          - " RECORDATORIOS IMPORTANTES:"
          - "   - Los secretos estan guardados de forma segura en .env"
          - "     (¡NUNCA COMMITEAR este archivo a Git!)"
          - "========================================================================"
'''

with open('site.yml', 'w', encoding='utf-8') as f:
    f.write(head + post_tasks)
