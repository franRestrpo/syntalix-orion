# Troubleshooting Chatwoot: Migrations & DB Auth

## Incidencia: 28 Abril 2026

### Descripción del Error
Durante el despliegue del servicio Chatwoot mediante Ansible (tarea `Esperar a que termine la migración`), el servicio `chatwoot_migrator` falló recurrentemente.
La inspección de los logs de Docker (contenedor `chatwoot_web`) reveló el siguiente error de Ruby/Rails:
`ActiveRecord::NoDatabaseError: We could not find your database: chatwoot.`

Posteriormente, el conector de Postgres arrojó:
`PG::ConnectionBad: connection to server at "10.0.1.13", port 5432 failed: FATAL:  password authentication failed for user "chatwoot"`

### Análisis
1. **Credenciales Mismatch**: El usuario `chatwoot` no pudo autenticarse en Postgres, lo que indica que la contraseña suministrada por Chatwoot no es la misma que la que espera Postgres.
2. **Race Condition / Dependencia**: Chatwoot intentaba ejecutar migraciones o arrancar antes de que Postgres estuviera completamente disponible y configurado.
3. **Duplicidad de Instancias**: Se observaron contenedores de `chatwoot_web` y `chatwoot_sidekiq`, lo cual es el comportamiento esperado (uno expone la app Rails en el puerto 3000, otro procesa jobs en background).

### Acciones Tomadas
1. **Centralización de variables**:
   En `group_vars/all/vars.yml`, se vincularon explícitamente las credenciales para evitar desajustes:
   ```yaml
   postgres_password: "{{ shared_postgres_password }}"
   POSTGRES_PASSWORD: "{{ shared_postgres_password }}"
   CHATWOOT_DB_PASSWORD: "{{ shared_db_password }}"
   ```
2. **Soporte para espera de DB**:
   Se agregó una tarea bajo `roles/wait_for_db/tasks/main.yml` que utiliza el módulo `wait_for` de Ansible para pausar el despliegue de la aplicación hasta que el puerto `5432` de Postgres responda de manera estable.

### Siguientes Pasos (Resolución Local)
1. Conectarse a Postgres y validar que el rol `chatwoot` tiene el password que figura en `vars.yml`. Si no, actualizarlo usando:
   `ALTER USER chatwoot WITH PASSWORD 'tu_password_central';`
2. Reiniciar el stack de Chatwoot (`docker service update --force chatwoot_web`).
3. Una vez se confirme que las migraciones pasan y el sistema levanta correctamente, este documento formará parte del pull request de soluciones.
