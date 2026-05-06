# Syntalix-Orion TUI - Diagramas de Flujo y Arquitectura

## 1. Arquitectura General del Sistema

```mermaid
flowchart TB
    subgraph TUI["TUI - Interfaz de Usuario"]
        direction TB
        selection["SelectionScreen<br/>Selección de Apps"]
        config["ConfigScreen<br/>Configuración de Variables"]
        deploy["DeployScreen<br/>Despliegue"]
    end

    subgraph State["StateStore - Gestión de Estado"]
        selected_apps["selected_apps: Set[str]"]
        user_variables["user_variables: Dict[str,str]"]
        deployment_plan["deployment_plan: DeploymentPlan"]
    end

    subgraph Core["Core Modules"]
        dependency_graph["DependencyGraph<br/>plan_with_vars_multi()"]
        models["models.py<br/>load_app_catalog()"]
        security["security.py<br/>Validaciones"]
        state["state.py<br/>load_env_file()<br/>save_env_file()"]
    end

    subgraph Metadata["Fuente de Verdad"]
        apps_metadata["apps_metadata.py<br/>APP_METADATA"]
    end

    subgraph Engine["Motor Ansible"]
        ansible_runner["ansible_runner_real.py<br/>RealAnsibleRunner"]
        site_yml["site.yml<br/>Playbook Maestro"]
    end

    subgraph Roles["Roles Ansible"]
        traefik_role["roles/core/traefik/"]
        grafana_role["roles/monitoring/grafana/"]
        other_roles["roles/*/"]
    end

    subgraph Output["Archivos de Configuración"]
        env_files[".env files<br/>traefik.env, grafana.env, etc."]
        stack_files["docker-stack.yml<br/>traefik_stack.yml, etc."]
    end

    %% TUI Flow
    selection -->|"SelectionComplete"| config
    config -->|"ConfigComplete"| deploy

    %% State interactions
    selection -->|"add_app() / remove_app()"| selected_apps
    config -->|"user_variables.update()"| user_variables
    config -->|"deployment_plan"| deployment_plan

    %% Config screen processing
    config -->|"plan_with_vars_multi(selected, existing_vars)"| dependency_graph
    dependency_graph -->|"vars_generated"| deployment_plan

    %% Metadata loading
    config -->|"load_app_catalog(APP_METADATA)"| models
    models -->|"catalog_dict"| dependency_graph

    %% State persistence
    config -->|"load_env_file(.env)"| state
    deploy -->|"save_env_file(.env, vars)"| state

    %% Ansible execution
    deploy -->|"run(vars_to_inject, modules)"| ansible_runner
    ansible_runner -->|"ansible-playbook site.yml -e @vars.json"| site_yml

    %% Role execution
    site_yml -->|"include_roles: traefik, grafana, ..."| traefik_role
    site_yml -->|"include_roles: grafana"| grafana_role
    site_yml -->|"include_roles: *"| other_roles

    %% Template rendering
    traefik_role -->|"template: traefik.env.j2 → traefik.env"| env_files
    traefik_role -->|"template: traefik.yml.j2 → traefik_stack.yml"| stack_files
    grafana_role -->|"template: grafana.env.j2 → grafana.env"| env_files
    grafana_role -->|"template: grafana.yml.j2 → grafana_stack.yml"| stack_files

    %% Styling
    class TUI fill:#1a1a2e,stroke:#00D9FF,color:#00D9FF
    class State fill:#16213e,stroke:#E94560,color:#E94560
    class Core fill:#0f3460,stroke:#00D9FF,color:#00D9FF
    class Metadata fill:#533483,stroke:#E94560,color:#E94560
    class Engine fill:#1a1a2e,stroke:#10B981,color:#10B981
    class Roles fill:#0f3460,stroke:#F59E0B,color:#F59E0B
    class Output fill:#16213e,stroke:#10B981,color:#10B981
```

---

## 2. Flujo Detallado: De TUI a Archivos .env

```mermaid
sequenceDiagram
    participant USER as Usuario (TUI)
    participant ConfigScreen as ConfigScreen
    participant StateStore as StateStore
    participant DependencyGraph as DependencyGraph
    participant State as state.py
    participant DeployScreen as DeployScreen
    participant AnsibleRunner as ansible_runner_real
    participant Ansible as Ansible
    participant Role as Role Task (ej: traefik)

    USER->>ConfigScreen: Ingresa dominio, usuario, password
    ConfigScreen->>ConfigScreen: _calculate_plan()
    ConfigScreen->>StateStore: selected_apps
    ConfigScreen->>State: load_env_file(.env)
    State-->>ConfigScreen: existing_vars

    ConfigScreen->>DependencyGraph: plan_with_vars_multi(['traefik'], existing_vars)
    Note over DependencyGraph: Mapea TRAEFIK__DOMAIN
    Note over DependencyGraph: Mapea TRAEFIK__USER
    Note over DependencyGraph: Mapea TRAEFIK__PASSWORD

    DependencyGraph-->>ConfigScreen: {vars: {TRAEFIK__USER: "miouser", TRAEFIK__PASSWORD: "mipass"}}
    ConfigScreen->>ConfigScreen: Genera formulario con defaults

    USER->>ConfigScreen: Modifica usuario/contraseña
    ConfigScreen->>ConfigScreen: on_input_changed()
    ConfigScreen->>StateStore: user_variables.update({TRAEFIK__USER: "miouser"})

    USER->>ConfigScreen: Confirma (Ctrl+Enter)
    ConfigScreen->>ConfigScreen: action_deploy()
    ConfigScreen->>ConfigScreen: _validate_inputs()
    ConfigScreen->>DeployScreen: ConfigComplete()

    DeployScreen->>DeployScreen: _start_deployment()
    DeployScreen->>State: save_env_file(.env, vars_to_inject)
    State-->>DeployScreen: OK

    DeployScreen->>AnsibleRunner: run(vars_to_inject, ['traefik'])
    AnsibleRunner->>AnsibleRunner: Crea .ansible_vars.json
    AnsibleRunner->>Ansible: ansible-playbook site.yml -e @.ansible_vars.json

    Ansible->>Role: Executing role traefik
    Role->>Role: lookup('vars', 'TRAEFIK__USER')
    Note over Role: Busca TRAEFIK__USER en extra vars
    Note over Role: Valor: "miouser"
    Role->>Role: set_fact app_actual
    Role->>Role: template traefik.env.j2 → traefik.env
    Role->>Role: template traefik.yml.j2 → traefik_stack.yml
```

---

## 3. Flujo de Variables: Formato APPID__VARIABLE

```mermaid
flowchart LR
    subgraph INPUT["Input TUI"]
        D["Dominio"]
        U["Usuario"]
        P["Contraseña"]
    end

    subgraph METADATA["apps_metadata.py"]
        TV["TRAEFIK_USER"]
        TP["TRAEFIK_PASSWORD"]
        TD["TRAEFIK_DASHBOARD_URL"]
    end

    subgraph MAP["map_app_variable()"]
        M1["TRAEFIK__USER"]
        M2["TRAEFIK__PASSWORD"]
        M3["TRAEFIK__DASHBOARD_URL"]
    end

    subgraph STATE["StateStore + .env"]
        S1["user_variables[TRAEFIK__USER]"]
        S2["user_variables[TRAEFIK__PASSWORD]"]
        S3["user_variables[TRAEFIK__DASHBOARD_URL]"]
    end

    subgraph ANSIBLE["Ansible extra-vars"]
        A1["TRAEFIK__USER=miouser"]
        A2["TRAEFIK__PASSWORD=mipass"]
        A3["TRAEFIK__DOMAIN=traefik.midominio.com"]
    end

    subgraph TEMPLATE_TASK["Role Task - traefik/tasks/main.yml"]
        T1["usuario_admin: {{ TRAEFIK__USER }}"]
        T2["password_db: {{ traefik_pwd_hash.stdout }}"]
        T3["dominio: {{ TRAEFIK__DASHBOARD_URL }}"]
    end

    subgraph APP_ACTUAL_SETFACT["ansible.builtin.set_fact: app_actual"]
        AC1["usuario_admin: miouser"]
        AC2["dominio: traefik.midominio.com"]
    end

    subgraph OUTPUT_TEMPLATES["Templates"]
        OT1["traefik.env.j2 → traefik.env"]
        OT2["traefik.yml.j2 → traefik_stack.yml"]
    end

    INPUT --> METADATA
    METADATA --> MAP
    MAP --> STATE
    STATE --> ANSIBLE
    ANSIBLE --> TEMPLATE_TASK
    TEMPLATE_TASK --> APP_ACTUAL_SETFACT
    APP_ACTUAL_SETFACT --> OUTPUT_TEMPLATES

    style INPUT fill:#1a1a2e,stroke:#00D9FF,color:#00D9FF
    style METADATA fill:#533483,stroke:#E94560,color:#E94560
    style MAP fill:#16213e,stroke:#F59E0B,color:#F59E0B
    style STATE fill:#16213e,stroke:#E94560,color:#E94560
    style ANSIBLE fill:#0f3460,stroke:#10B981,color:#10B981
    style TEMPLATE_TASK fill:#1a1a2e,stroke:#00D9FF,color:#00D9FF
    style APP_ACTUAL_SETFACT fill:#0f3460,stroke:#F59E0B,color:#F59E0B
    style OUTPUT_TEMPLATES fill:#16213e,stroke:#10B981,color:#10B981
```

---

## 4. Máquina de Estados - StateStore

```mermaid
stateDiagram-v2
    [*] --> SelectionScreen: app.start()
    SelectionScreen --> SelectionScreen: add_app() / remove_app()

    state SelectionScreen {
        [*] --> Empty
        Empty --> Selected: add_app()
        Selected --> Selected: add_app() / remove_app()
        Selected --> Empty: clear_selections()
    }

    SelectionScreen --> ConfigScreen: SelectionComplete
    ConfigScreen --> ConfigScreen: _calculate_plan()

    state ConfigScreen {
        [*] --> CalculatingPlan
        CalculatingPlan --> FormReady: plan generado
        FormReady --> FormReady: on_input_changed()
        FormReady --> Validating: confirm button
        Validating --> FormReady: validation error
        Validating --> ConfigComplete: validación OK
    }

    ConfigScreen --> DeployScreen: ConfigComplete
    DeployScreen --> [*]: Despliegue completo

    state DeployScreen {
        [*] --> SavingEnv
        SavingEnv --> RunningAnsible: .env guardado
        RunningAnsible --> Done: Ansible OK
        RunningAnsible --> Failed: Ansible FAIL
    }
```

---

## 5. Detalle del Role Ansible - Traefik

```mermaid
flowchart TB
    subgraph INPUTS["Inputs del Role"]
        E1["TRAEFIK__USER"]
        E2["TRAEFIK__PASSWORD"]
        E3["TRAEFIK__DASHBOARD_URL"]
        E4["TRAEFIK__ACME_EMAIL"]
    end

    subgraph TASK_SETUP["traefik : tasks/main.yml"]
        T1["file: crear deploy/"]
        T2["shell: generar hash bcrypt"]
        T3["set_fact: app_actual"]
        T4["shell: docker volume create"]
        T5["template: traefik.env.j2"]
        T6["template: traefik.yml.j2"]
        T7["command: docker stack deploy"]
    end

    subgraph APP_ACTUAL["app_actual object"]
        A1["nombre: traefik"]
        A2["dominio: {{ TRAEFIK__DASHBOARD_URL }}"]
        A3["usuario_admin: {{ TRAEFIK__USER }}"]
        A4["password_db: {{ hash_bcrypt }}"]
        A5["acme_email: {{ TRAEFIK__ACME_EMAIL }}"]
    end

    subgraph TEMPLATES["Templates"]
        TP1["traefik.env.j2"]
        TP2["traefik.yml.j2"]
    end

    subgraph OUTPUTS["Outputs"]
        O1["deploy/traefik.env"]
        O2["deploy/traefik_stack.yml"]
    end

    INPUTS --> T3
    T2 --> A4
    T3 --> APP_ACTUAL
    APP_ACTUAL --> TP1
    APP_ACTUAL --> TP2
    TP1 --> O1
    TP2 --> O2

    style INPUTS fill:#1a1a2e,stroke:#00D9FF,color:#00D9FF
    style TASK_SETUP fill:#0f3460,stroke:#F59E0B,color:#F59E0B
    style APP_ACTUAL fill:#16213e,stroke:#E94560,color:#E94560
    style TEMPLATES fill:#533483,stroke:#10B981,color:#10B981
    style OUTPUTS fill:#16213e,stroke:#10B981,color:#10B981
```

---

## 6. Template traefik.env.j2 - Renderizado

```mermaid
flowchart LR
    subgraph TEMPLATE["traefik.env.j2"]
        L1["INTERNAL_NETWORK=SyntalixNet"]
        L2["ACME_EMAIL={{ app_actual.acme_email }}"]
        L3["TRAEFIK_DASHBOARD_URL={{ app_actual.dominio }}"]
        L4["TRAEFIK_USER={{ app_actual.usuario_admin }}"]
        L5["TRAEFIK_PASSWORD={{ app_actual.password_db }}"]
    end

    subgraph CONTEXT["app_actual (desde set_fact)"]
        C1["acme_email: admin@test.com"]
        C2["dominio: traefik.test.com"]
        C3["usuario_admin: admin"]
        C4["password_db: $2b$12$hash..."]
    end

    subgraph RENDERED["traefik.env (resultado)"]
        R1["INTERNAL_NETWORK=SyntalixNet"]
        R2["ACME_EMAIL=admin@test.com"]
        R3["TRAEFIK_DASHBOARD_URL=traefik.test.com"]
        R4["TRAEFIK_USER=admin"]
        R5["TRAEFIK_PASSWORD=$2b$12$hash..."]
    end

    TEMPLATE + CONTEXT --> RENDERED
```

---

## 7. Flujo Completo: Selección → Despliegue

```mermaid
flowchart TB
    subgraph START["1. Selección en TUI"]
        A1["Usuario marca Traefik + Grafana"]
        A2["auto-dependencies: CrowdSec, Postgres"]
    end

    subgraph CONFIG["2. ConfigScreen"]
        B1["load_env_file(.env)"]
        B2["plan_with_vars_multi(['traefik','grafana'])"]
        B3["Genera formulario con vars"]
        B4["Usuario ingresa: dominio, user, pass"]
        B5["user_variables[TRAEFIK__USER]=miouser"]
        B6["user_variables[TRAEFIK__PASSWORD]=mipass"]
    end

    subgraph DEPLOY["3. DeployScreen"]
        C1["save_env_file(.env, vars_to_inject)"]
        C2["chmod 600 .env"]
        C3["AnsibleRunner.run(vars, modules)"]
        C4["Crea .ansible_vars.json"]
    end

    subgraph ANSIBLE["4. Ansible Execution"]
        D1["ansible-playbook site.yml -e @vars.json"]
        D2["include_roles: [traefik, grafana, ...]"]
        D3["set_fact: app_actual para cada role"]
    end

    subgraph TRAEFIK_ROLE["5. Role: traefik"]
        E1["lookup('vars', 'TRAEFIK__USER')"]
        E2["set_fact: app_actual"]
        E3["template: traefik.env.j2 → deploy/traefik.env"]
        E4["template: traefik.yml.j2 → deploy/traefik_stack.yml"]
        E5["docker stack deploy -c traefik_stack.yml traefik"]
    end

    subgraph GRAFANA_ROLE["6. Role: grafana"]
        F1["lookup('vars', 'GRAFANA__USER')"]
        F2["set_fact: app_actual"]
        F3["template: grafana.env.j2 → deploy/grafana.env"]
        F4["template: grafana.yml.j2 → deploy/grafana_stack.yml"]
        F5["docker stack deploy -c grafana_stack.yml grafana"]
    end

    subgraph END["7. Resultado"]
        G1["traefik.env con credenciales correctas"]
        G2["grafana.env con credenciales correctas"]
        G3["Stacks desplegados en Swarm"]
    end

    START --> CONFIG
    CONFIG --> DEPLOY
    DEPLOY --> ANSIBLE
    ANSIBLE --> TRAEFIK_ROLE
    ANSIBLE --> GRAFANA_ROLE
    TRAEFIK_ROLE --> END
    GRAFANA_ROLE --> END
```

---

## 8. Mapa de Transformación de Variables

```mermaid
flowchart LR
    subgraph TRAEFIK["Traefik"]
        direction TB
        T1["apps_metadata:<br/>TRAEFIK_USER"]
        T2["map_app_variable() →<br/>TRAEFIK__USER"]
        T3["ConfigScreen<br/>input value"]
        T4["StateStore<br/>user_variables"]
        T5[".env file"]
        T6["Ansible extra-vars<br/>TRAEFIK__USER"]
        T7["role: traefik<br/>lookup vars"]
        T8["set_fact app_actual<br/>usuario_admin"]
        T9["traefik.env.j2<br/>TRAEFIK_USER={{ usuario_admin }}"]
        T10["traefik.env<br/>TRAEFIK_USER=miouser"]
    end

    T1 --> T2 --> T3 --> T4 --> T5 --> T6 --> T7 --> T8 --> T9 --> T10

    style Traefik fill:#1a1a2e,stroke:#00D9FF,color:#00D9FF
```

```mermaid
flowchart LR
    subgraph GRAFANA["Grafana"]
        direction TB
        G1["apps_metadata:<br/>GRAFANA_USER, GRAFANA_PASSWORD"]
        G2["map_app_variable() →<br/>GRAFANA__USER, GRAFANA__PASSWORD"]
        G3["ConfigScreen<br/>input values"]
        G4["StateStore<br/>user_variables"]
        G5[".env file"]
        G6["Ansible extra-vars<br/>GRAFANA__USER, GRAFANA__PASSWORD"]
        G7["role: grafana<br/>lookup vars"]
        G8["set_fact app_actual<br/>usuario_admin, password_db"]
        G9["grafana.env.j2<br/>GRAFANA_USER={{ usuario_admin }}<br/>GRAFANA_PASSWORD={{ password_db }}"]
        G10["grafana.env<br/>GRAFANA_USER=admin<br/>GRAFANA_PASSWORD=secure123"]
    end

    G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> G7 --> G8 --> G9 --> G10

    style Grafana fill:#1a1a2e,stroke:#10B981,color:#10B981
```

---

## Resumen de Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `apps_metadata.py` | Fuente de verdad - catálogo de apps y variables |
| `state_store.py` | Gestor de estado centralizado de la TUI |
| `dependency_graph.py` | Motor de resolución de dependencias y generación de vars |
| `config.py` | Pantalla de configuración - captura input del usuario |
| `deploy.py` | Pantalla de despliegue - ejecuta Ansible |
| `ansible_runner_real.py` | Ejecutor de Ansible via subprocess |
| `site.yml` | Playbook maestro que incluye roles |
| `roles/*/tasks/main.yml` | Tasks de cada role que hacen set_fact y template |
| `roles/*/templates/*.j2` | Templates Jinja2 que generan .env y docker-compose |