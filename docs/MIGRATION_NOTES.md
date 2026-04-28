Notas de Migración: YAML a UI TUI (Syntalix-Orion)

Resumen
- Objetivo: migrar de edición manual de YAML a una experiencia de usuario de terminal guiada que orqueste despliegues.
- Alcance: fases 2 (UI Textual) y 3 (Ansible central vars); plan para ansible-runner real y grafo de dependencias.

Guía de migración
1) Preparación de entorno
- Verificar que existan playbooks y roles actuales y que puedan consumir extravars desde vars centralizados.
- Centralizar credenciales en group_vars/all/vars.yml o Vault; evitar duplicación de secretos.
- Establecer un grafo de dependencias para orquestar despliegues y detectar ciclos.

2) Diseño de la UI
- El flujo debe guiar al usuario desde la entrada de parámetros (IP Proxmox, token, usuario) a la selección de módulos y lanzamiento del despliegue.
- Persistir estado de la sesión para reanudación (state.json).
- Incluir modo debug para ver salida cruda del runner (p. ej., pulsando F12).

3) Implementación y migración gradual
- Phase 2: completar la UI Textual, con mock de DependencyGraph y plan de despliegue.
- Phase 3: integrar AnsibleRunner real; consumir vars centralizados; eliminar duplicación de secretos.
- Mantener fallback a mock para entornos donde ansible-runner no esté disponible.

4) Seguridad y cumplimiento
- Restricción de logs de secrets; usar Vault o secret store para credenciales sensibles.
- No exponer puertos HTTP a través de la UI; todo pasa por el proxy/Traefik según el diseño.

5) Pruebas y validación
- Pruebas unitarias para DependencyGraph y listeners de runner.
- Pruebas de flujo end-to-end de la UI, con casos de éxito y fallo.
- Pruebas de migración: comparar resultados entre YAML tradicional y la UI para un subconjunto de despliegues.

6) Plan de rollback
- Mantener un modo fallback a mock y registrar en logs para auditoría.
- Instrucciones para revertir cambios si la migración no es estable.

7) Cronograma sugerido
- Semanas 1-2: Preparación, plan y start de Phase 2 (UI + mock graph)
- Semanas 3-4: Phase 3: integración del runner real (con fallback)
- Semana 5: pruebas de integración y CI
- Semana 6: documentación y migración de usuarios

Notas finales
- Este documento sirve como guía de alto nivel; se complementa con planes detallados en docs PLAN_ANSIBLE_RUNNER_REAL.md y docs PR_CHECKLIST.md.
