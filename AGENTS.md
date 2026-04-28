# AGENTS.md
// Este archivo contiene directrices en forma de preguntas-respuestas para guiar a los agentes OpenCode.
// Cada línea responde a la pregunta: "Would an agent likely miss this without help?".
// Se incluye solo si la respuesta es afirmativa (Sí); de lo contrario se omite.

- Sí: apps_metadata.py debe ser la fuente de verdad principal del catálogo de apps; sin ella el DependencyGraph carece de datos consistentes.
- Sí: DependencyGraph debe poder cargar apps_metadata y resolver dependencias transitivas; sin ello, el plan de despliegue no sería determinista.
- Sí: Debe deduplicar contraseñas de base de datos; POSTGRES_PASSWORD debe existir solo en la entrada de postgres_pgvector, y no repetirse en Chatwoot, Odoo, ni Dify.
- Sí: La contraseña de Postgres debe ser generada de forma central (global) y repartida entre apps que la necesiten, en lugar de generar una por app.
- Sí: Dify no debe declarar DB_PASSWORD; Chatwoot no debe declarar POSTGRES_PASSWORD; Odoo no debe declarar POSTGRES_PASSWORD; Flowise y ActivePieces deben incluir dependencias de persistencia (Postgres_pgvector, Redis, etc.).
- Sí: Evolution API debe incluir MongoDB como dependencia obligatoria, y leer su API key de forma segura.
- Sí: Flowise y ActivePieces deben depender de al menos Postgres_pgvector y Redis para persistencia; no deben funcionar sin almacenamiento persistente.
- Sí: Chatwoot debe declarar RabbitMQ como dependencia obligatoria (para colas) y no depender solo de Redis para cola.
- Sí: Las transformaciones de secretos con bcrypt deben limitarse a secretos de aplicación (como credenciales UI) y no aplicarse a contraseñas de bases de datos (POSTGRES_PASSWORD, MYSQL_ROOT_PASSWORD, etc.).
- Sí: Los secretos deben generarse críptograficamente (usando secrets.token_urlsafe) y las contraseñas DB deben conservarse en texto plano seguro o en Vault, no como hashes bcrypt en el env de DB.
- Sí: La salida del motor debe generar un archivo maestro vars.yml (o .env) consolidando credenciales; las apps deben consumir este único source de verdad para claves de DB compartidas.
- Sí: El motor debe sumar RAM total para el plan (RAM por app + dependencias) y emitir una advertencia crítica si excede un umbral configurado (p. ej. 8 GB).
- Sí: Todas las apps web deben quedar detrás de Traefik; generar etiquetas Docker dinámicas para TLS y políticas de seguridad cuando se seleccione una app.
- Sí: No exponer puertos al host para apps HTTP; todo debe pasar por Traefik (proxy inverso).
- Sí: Las apps de valor deben estructurarse con dependencias realistas (Flowise/ActivePieces requieren persistencia; Evolution API requiere MongoDB; Chatwoot requiere RabbitMQ; Flowise/OpenWebUI/Flowise deben conectarse a Postgres/Redis para persistencia).
- Sí: El catálogo debe organizarse por capas (Core, Data, Monitoring, Apps de Valor) con RAM y dependencias claras para facilitar el grafo.
- Sí: El grafo debe detectar ciclos de dependencias y reportarlos para evitar despliegues inválidos.
- Sí: Incluir recomendaciones para pruebas de DependencyGraph (unit tests básicas que validen resolución de dependencias y generación de vars).
- Sí: Documentar el flujo objetivo de la Fase 2: UI Textual que consume el grafo, genera RAM en tiempo real y produce vars.yml.
- Sí: Añadir ejemplos prácticos de DependencyGraph para pruebas rápidas (escenarios como Traefik+Portainer, Dify con dependencias, Chatwoot con RabbitMQ, y casos de fallo por duplicación de secretos).
- Sí: Proporcionar comandos de verificación rápida para pruebas (p. ej., ejecutar scripts de prueba o pytest) y entender salidas esperadas.
- Sí: Incluir una pequeña sección de validación de seguridad para Contraseñas y secretos (evitar bcrypt en DB y centralizar secretos).
