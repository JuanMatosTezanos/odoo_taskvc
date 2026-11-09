# Dev Projects para Odoo 17

Gestión de proyectos de software al estilo Jira, construida sobre la app **Proyecto** (Project) de Odoo.

> **¿Solo vas a usar la app?** Lee la [Guía de usuario](GUIA_DE_USUARIO.md) en lenguaje sencillo ([User Guide in English](USER_GUIDE.md)). Este README es para quienes la instalan y la mantienen.

Dev Projects añade claves de incidencia (`WEB-1`, `WEB-2`…), tipos de incidencia, subtareas, un **Tablero** con límites WIP, un backlog ordenado, sprints que se inician y se completan a mano (con un resumen de cada uno), hitos con versión, componentes, tecnologías y perfiles de desarrollador. Un **icono de tickets** (📢) en la barra superior permite que cualquier persona de la empresa envíe problemas, ideas y pedidos de TI al equipo, que los atiende en su propio tablero de tickets. Trabaja sobre **los mismos proyectos y tareas** que la app Proyecto. Una incidencia es una tarea normal de Odoo con campos extra, así que puedes cambiar entre las dos apps en cualquier momento. Todo el módulo está disponible en **inglés y español**.

> Este README usa los nombres de la app en español. Si tu Odoo está en inglés, la [tabla de idiomas](#idiomas-inglés--español) muestra cómo se llama cada pantalla.

---

## Contenido

- [Funcionalidades](#funcionalidades)
- [Cómo encaja con la app Proyecto](#cómo-encaja-con-la-app-proyecto)
- [Primeros pasos](#primeros-pasos)
- [Flujo de trabajo diario](#flujo-de-trabajo-diario)
- [Configuración](#configuración)
- [Idiomas (inglés / español)](#idiomas-inglés--español)
- [Ejecutar las pruebas](#ejecutar-las-pruebas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desinstalar](#desinstalar)

---

## Funcionalidades

**Incidencias**
- Tipos: Historia, Tarea, Error, Mejora.
- Una clave por proyecto, p. ej. `AG-1`, `AG-2`. Se sugiere a partir del nombre del proyecto ("AI glasses" → `AG`) y se puede buscar por ella.
- Puntos de historia, una prioridad de 4 niveles (Normal, Importante, Alta, Crítica) y una gravedad para los errores.
- Un **responsable** (que también se añade a los asignados de la tarea en Odoo) y un **Reportado por** (quien la creó).
- Fechas de inicio y fin que se rellenan automáticamente a medida que la incidencia avanza por el tablero.
- Pausar/reanudar, avisos de vencimiento y **Completar**: marcarla como hecha y después archivarla o eliminarla.

**Subtareas**
- Divide una incidencia en pasos más pequeños en su pestaña **Subtareas**. Se muestran justo debajo de la incidencia principal.
- Cada subtarea recibe su propia clave (p. ej. `AG-7`) y sigue el sprint de su incidencia principal. También toma el componente de la principal si no tiene uno, y lo sigue cuando ese componente cambia (salvo que se le haya puesto otro a propósito).
- Las subtareas no tienen tarjeta propia en el **Tablero** ni fila en el Backlog. En su lugar, la tarjeta de la principal muestra un contador, p. ej. **☑ 2/5** (subtareas hechas / total), y las listas muestran "(2/5 subtareas)" junto al nombre.
- No cuentan por sí solas en las cifras de sprints, hitos, componentes y proyectos, ni ocupan un hueco del límite WIP: cuenta la principal. Por eso tampoco tienen puntos de historia.

**Tablero**
- Las columnas son etapas de proyecto de Odoo, cada una con una categoría de estado: Por hacer, En curso, En revisión o Hecho.
- Mover una tarjeta a una columna Hecho marca la tarea como hecha también en la app Proyecto, y sacarla de ahí la reabre.
- **Límite WIP** opcional por columna, contado por proyecto y sprint. Las columnas Hecho nunca tienen límite.
- Muestra el **trabajo actual**: el sprint en curso más las incidencias que no están en ningún sprint.
- **Lo más importante primero** en cada columna: errores Críticos/Bloqueantes, luego por prioridad Dev (Crítica → Alta → Importante → Normal), luego el orden del backlog.

**Backlog y sprints**
- Backlog agrupado por sprint. Arrastra para ordenar las incidencias y elige un sprint para planificarlas.
- Los sprints se inician y se completan a mano, como en Jira. Solo puede haber un sprint en curso por proyecto.
- Al completar un sprint, las incidencias sin terminar pasan al siguiente sprint o vuelven al backlog.
- Progreso del sprint, puntos planificados y puntos hechos.

**Resumen del sprint**
- Al completar un sprint se abre su **resumen**:
  - incidencias y puntos de historia terminados, sobre lo que había en el sprint al final;
  - lo terminado por tipo (historias, errores corregidos…), por componente y por persona;
  - las incidencias terminadas, y las que quedaron sin terminar con su destino (siguiente sprint o backlog);
  - un cuadro **Notas del sprint** donde el equipo escribe de qué trató el sprint.
- El resumen se guarda en el sprint. Un sprint cerrado se abre en su pestaña **Resumen**, así que puedes leerlo o editar las notas más tarde.
- Es una foto tomada al completarlo, así que no cambia si las incidencias cambian después.

**Hitos (milestones)**
- Un hito es un objetivo con fecha límite, p. ej. *"Login completo — 20 nov"*. Agrupa **sprints** e **incidencias**:
  ```
  Proyecto: AI glasses
  └─ Hito: Login completo (v1.2.0, vence 20 nov)   ███░░ 60%
     ├─ Sprint 1 → AG-1 Historia: formulario de login, AG-2 Error: mensaje de contraseña incorrecta
     └─ Sprint 2 → AG-3 Mejora: login con Google
  ```
- Una **Versión** opcional por hito, p. ej. `1.2.0`. Solo acepta números de versión: `1.0`, `1.2.0`, `v2.0.1`, o con una etiqueta como `2.1.0-beta`.
- Vincula un sprint a un hito y todas las incidencias de ese sprint se unen al hito automáticamente. También se puede asignar un hito directamente a una incidencia.
- Cada hito muestra su progreso (incidencias y puntos de historia hechos), errores y tecnologías usadas. Se pone en rojo con una cinta **Atrasado** al pasar su fecha límite, y tiene un botón **Marcar como completado**.
- Son los hitos propios de Odoo, así que la app Proyecto muestra los mismos.

**Proyectos**
- Un enlace **Repositorio de GitHub** en cada proyecto de software.
- El formulario del proyecto tiene las pestañas **Desarrollo | Hitos | Sprints | Componentes | Descripción | Ajustes**. Hitos, Sprints y Componentes solo aparecen en los proyectos de software.
- Los proyectos de software llaman a sus tareas **Incidencias** y ocultan los campos "Nombre de las tareas" y Etiquetas de Odoo. El botón **Tareas** de Odoo se sustituye por **Incidencias abiertas**, y el botón **Tablero** abre el tablero.

**Componentes**
- Los componentes son las partes de tu software, p. ej. *Login*, *Pagos*, *Cámara*. Cada proyecto tiene su propia lista.
- Elige uno en el campo **Componente** de una incidencia (debajo de Prioridad dev). Si escribes un nombre nuevo, te ofrece crearlo en el momento.
- Cada componente tiene un **Responsable** opcional y muestra sus incidencias, incidencias abiertas, errores abiertos y tecnologías usadas. Las tarjetas del Tablero, las listas de incidencias y el Backlog muestran el componente, y puedes filtrar o agrupar por él.
- Al duplicar un proyecto también se copian sus componentes.
- En el código, los componentes se siguen llamando módulos (modelo `dev.module`, campo `dev_module_id`), porque ese fue su primer nombre. Solo cambiaron las etiquetas, así que no hubo que mover datos.

**Tecnologías y desarrolladores**
- Las tecnologías obtienen su logo automáticamente de una carpeta de imágenes (`Docker` → `Docker.png`).
- Perfiles de desarrollador en los contactos:
  - Un código de acceso: 8 dígitos seguidos de letras, p. ej. `12345678A`. Debe ser único y no se puede cambiar una vez guardado.
  - Las tecnologías que conoce el desarrollador.
  - Una etiqueta "Devs", que se añade automáticamente.
  - Un botón **Crear usuario** que da al desarrollador un acceso a Odoo (su email), para poder asignarle incidencias. Vincula el acceso al mismo contacto, así que el perfil se conserva.

**Tickets (para quienes no son del equipo)**

Los tickets son problemas, ideas y preguntas que las personas de la empresa envían al equipo (desarrolladores y TI). Viven en su **propio tablero** y nunca entran en proyectos, backlogs ni sprints. Proyectos Dev queda para el trabajo scrum del propio equipo.

*Enviar (todos):*
- Un icono 📢 en la barra superior, junto al chat y las actividades, en todas las pantallas y para todos los usuarios internos. Quienes no tienen permisos de Proyecto no necesitan (ni ven) la app Proyectos.
- El menú del icono tiene **Nuevo ticket** y **Mis tickets**.
- **Nuevo ticket** abre un formulario emergente:
  - *Reportado por* (ya rellenado)
  - **¿De qué se trata?**: *Una aplicación de Odoo* o *Soporte de TI* (computadora, impresora, internet, correo, contraseñas)
  - **Aplicación** (en los tickets de aplicación): la app de Odoo donde ocurre, p. ej. Ventas. Es obligatoria y solo muestra las apps instaladas que esa persona puede abrir, así que un trabajador normal nunca ve Proyectos Dev.
  - *¿Qué es?*: Algo no funciona / Pedir una función nueva / Pregunta
  - Título y detalles (se pueden pegar capturas de pantalla). Con *Algo no funciona*, una nota breve pide los pasos: dónde hizo clic, qué esperaba y qué pasó en cambio.
  - *¿Qué tan urgente es?*: Puede esperar / Normal / Urgente / No puedo trabajar
  - **Enviar** lo guarda y muestra su número, p. ej. *TCK-12*.
- **Mis tickets** lista lo que enviaste y en qué punto está: *Esperando revisión → Aceptado → En curso → Hecho*, o *Rechazado* con el motivo. Cada persona solo ve sus propios tickets.
- **Sigue sin funcionar:** durante 7 días después de terminado, quien lo envió puede devolverlo a Por hacer con un comentario.
- Quien envía el ticket lo sigue y recibe un aviso cuando se acepta, se rechaza y se termina.

*Atender (el equipo): Proyectos Dev → Trabajo → Tickets*
- Un tablero con **Nuevo → Por hacer → En curso → Hecho**, lo más urgente primero en cada columna. Los tickets rechazados se ocultan; el filtro *Rechazados* los muestra.
- La opción **Tickets** del menú muestra cuántos tickets nuevos están esperando, p. ej. *Tickets 3*.
- **Aceptar** pasa un ticket nuevo a Por hacer; **Rechazar** pide un motivo, que ve quien lo envió. **Revisar de nuevo** devuelve uno rechazado a Nuevo. También se pueden arrastrar las tarjetas entre columnas.
- **Asignado a**: quién del equipo lo atiende, con un botón **Asignarme**. Quien pasa un ticket a En curso se lo queda si nadie lo tiene.
- Cada ticket tiene un número (**TCK-1**, **TCK-2**…) que se puede buscar.
- Los tickets **Urgente** y **No puedo trabajar** avisan a todo el equipo en cuanto se envían.
- Filtros: Nuevo, Abiertos, Asignados a mí, Sin asignar, TI, Aplicaciones, Urgente. Selecciona varios y usa **Acciones → Aceptar** para aceptarlos de una vez.
- El equipo son todas las personas con permisos de usuario de Proyecto, así que dale esos permisos también a la persona de TI.

---

## Cómo encaja con la app Proyecto

Tras la instalación, la pantalla de inicio muestra una sola app **Proyectos** (para el equipo de desarrollo) con dos menús. Los demás usan el icono 📢 de tickets de la barra superior (ver [Funcionalidades](#funcionalidades)).

```
Proyectos  |  Proyecto ▾          |  Proyectos Dev ▾
           |  Menús propios de    |  Planificación: Proyectos, Hitos, Sprints, Componentes
           |  Odoo, sin cambios   |  Trabajo:       Tablero, Backlog, Tickets
           |                      |  Equipo:        Mi perfil de desarrollador, Desarrolladores, Tecnologías
           |                      |  Configuración
```

- Los **proyectos de software** tienen marcada la casilla *Proyecto de software*. Los proyectos creados desde Proyectos Dev la tienen marcada automáticamente. Solo estos aparecen en Proyectos Dev y reciben claves, columnas del tablero y el comportamiento de Dev.
- Los **proyectos normales** (marketing, oficina, etc.) se comportan exactamente como en Odoo estándar.
- La app Proyecto oculta por defecto los proyectos de software con un filtro **"Ocultar proyectos de software"**. Es un filtro de búsqueda normal, así que al quitarlo se ve todo.
- Para pasar un proyecto existente a Proyectos Dev, marca *Proyecto de software* en él. Recibe una clave y columnas del tablero, y sus tareas existentes se numeran.

---

## Primeros pasos

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose)

### 1. Iniciar Odoo

Desde la carpeta del proyecto:

```bash
docker compose up -d
```

Esto inicia dos contenedores:

| Contenedor          | Qué es                  | Puerto |
|---------------------|-------------------------|--------|
| `odoo_dev_web`      | Odoo 17                 | 8069   |
| `odoo_dev_database` | PostgreSQL 17           | (interno) |

Abre **http://localhost:8069**.

### 2. Crear una base de datos

Si todavía no tienes una base de datos, Odoo muestra el gestor de bases de datos. Crea una (por ejemplo `ProjectsData`) e inicia sesión.

### 3. Instalar el módulo

1. Ve a **Aplicaciones** (Apps).
2. Quita el filtro "Aplicaciones" y busca **Dev Projects**.
3. Haz clic en **Activar**.

La app **Proyecto** se instala automáticamente si no la tienes.

### Después de cambiar el código

- **Cambios en Python:** reinicia el contenedor web con `docker restart odoo_dev_web`.
- **Cambios en vistas/XML, campos o traducciones:** actualiza el módulo, desde *Aplicaciones → Dev Projects → Actualizar* o desde la línea de comandos:

  ```bash
  docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
      -d ProjectsData -u dev_addons --stop-after-init
  docker restart odoo_dev_web
  ```

> **Nombre del módulo:** la carpeta del módulo es `dev_addons/` misma, así que su nombre técnico es **`dev_addons`** (en Aplicaciones aparece como "Dev Projects"). Docker la monta en `/mnt/extra-addons/dev_addons`. Las bases de datos antiguas que lo instalaron como `dev_projects` necesitan renombrar el módulo antes de actualizar.

---

## Flujo de trabajo diario

**En una línea:** configura Componentes e Hitos → escribe incidencias en el **Backlog** → planifica e **inicia** un sprint → arrastra tarjetas en el **Tablero** → **Completar sprint** y lee el resumen → repite → **marca el hito como completado**.

Cómo encajan las piezas:

```
Proyecto: AI glasses
├─ Hitos        → ¿POR QUÉ / qué objetivo?   "Login completo" (v1.2.0), "Lanzamiento beta"
├─ Sprints      → ¿CUÁNDO se hace?           "Sprint 1", "Sprint 2"
└─ Componentes  → ¿QUÉ parte es?             "Login", "Cámara", "UI"
```

Una incidencia puede tener las tres, p. ej. **AG-4 Error: Mensaje de contraseña incorrecta**, con Hito *Login completo*, Sprint *Sprint 1* y Componente *Login*. Las incidencias grandes se pueden dividir en subtareas.

### 1. Configura el proyecto (una vez)
*Proyectos Dev → Planificación → Proyectos → Nuevo*. Escribe el nombre y guarda; recibe una clave (p. ej. `AG`) y columnas del tablero. Después rellena las pestañas:
- **Desarrollo:** revisa la clave y pega el enlace **Repositorio de GitHub**.
- **Componentes:** añade las partes de tu app con **Agregar línea**, p. ej. *Login, Cámara, UI*.
- **Hitos:** añade tus objetivos grandes con fecha límite y, si quieres, la versión con la que salen, p. ej. *"Lanzamiento beta — 1 dic — 1.0.0"*.

### 2. Anota el trabajo (en cualquier momento)
*Trabajo → **Backlog***
- **Agregar línea** por cada cosa que hacer y elige su tipo: Historia, Tarea, Error o Mejora.
- Asigna su **Componente**.
- Arrastra las líneas para dejar las más importantes arriba.
- Para una incidencia grande, ábrela (**Ver** al final de la línea) y añade pasos en su pestaña **Subtareas**.
- Revisa *Trabajo → **Tickets*** para ver lo que enviaron personas de fuera del equipo. Los tickets tienen su propio tablero y nunca entran en el backlog.

### 3. Planifica un sprint (cada 1–2 semanas)
En la pestaña **Sprints** del proyecto, o en *Planificación → Sprints*:
1. Crea un sprint y elige el **Hito** al que contribuye.
2. En el **Backlog**, rellena la columna **Sprint** en las incidencias que vas a hacer. Se unen automáticamente al hito del sprint, y sus subtareas van con ellas.
3. Abre el sprint y haz clic en **Iniciar sprint**.

### 4. Haz el trabajo (cada día)
*Trabajo → **Tablero***
- Arrastra tarjetas: **Por hacer → En curso → En revisión → Hecho**. Cada columna muestra primero las tarjetas más importantes.
- Las incidencias nuevas creadas aquí entran directamente en el sprint en curso.

### 5. Termina el sprint
Abre el sprint y haz clic en **Completar sprint**. Las incidencias sin terminar pasan al siguiente sprint o vuelven al backlog. Se abre el **resumen**: revisa las cifras, escribe unas notas y haz clic en **Guardar**. Luego repite desde el paso 3.

### 6. Termina el hito
Cuando se alcance su objetivo, ábrelo (pestaña **Hitos** del proyecto) y haz clic en **Marcar como completado**.

**Botones que puedes ignorar al principio**
- **Iniciar / Enviar a revisión / Marcar como hecha** en una incidencia hacen lo mismo que arrastrar su tarjeta.
- **Pausar / Reanudar** y **Asignarme** son atajos pequeños.
- **Completar** en una incidencia la marca como hecha *y* quita la tarjeta del Tablero (archivar o eliminar). Úsalo solo cuando quieras que desaparezca.
- **Reabrir** es solo para algo marcado como hecho por error.
- El menú **Proyecto** es la app normal de Odoo para proyectos que no son de software. Puedes trabajar solo en **Proyectos Dev**.

> **¿Por qué no veo las incidencias de mi sprint en el Tablero?**
> El Tablero muestra el sprint *en curso* más las incidencias que no están en ningún sprint. Las incidencias de un sprint que no se ha iniciado quedan ocultas hasta que haces clic en **Iniciar sprint**. Para verlas antes, usa el botón **Incidencias** del sprint o quita el filtro "Trabajo actual".
>
> Si creas una incidencia en el Tablero sin ningún sprint en curso, va al backlog y una breve notificación te lo indica.
>
> Las subtareas nunca tienen tarjeta propia: abre la incidencia principal para verlas.

---

## Configuración

**Ajustes → Proyecto → Dev Projects**

| Ajuste | Por defecto | Qué hace |
|--------|-------------|----------|
| Carpeta de logotipos de tecnologías | `/tech_images` | Carpeta donde se buscan los logos `<Nombre de tecnología>.png` |
| Duración predeterminada del sprint (días) | 14 | Duración de los sprints nuevos |
| Columnas del tablero predeterminadas para nuevos proyectos de software | Activado | Da a los proyectos de software nuevos las cuatro columnas por defecto |

**Proyectos Dev → Configuración → Columnas del tablero**: renombra, reordena o añade columnas, y define la *Categoría de estado* y el *Límite WIP* de cada columna (0 = sin límite).

**Logos de tecnologías**: pon archivos PNG en [`tech_images/`](tech_images/). El nombre del archivo debe coincidir con el nombre de la tecnología, sin importar mayúsculas o minúsculas. La carpeta se monta en solo lectura dentro del contenedor en `/tech_images`.

---

## Idiomas (inglés / español)

Todas las pantallas, botones, mensajes y las columnas por defecto están traducidos al español ([`i18n/es.po`](dev_addons/i18n/es.po)). Las pantallas propias de Odoo ya vienen en español. El idioma se elige **por usuario**, así que una persona puede trabajar en inglés y otra en español.

1. **Una vez, como administrador:** *Ajustes → Ajustes generales → Idiomas → Agregar idiomas*, elige un español (p. ej. *Spanish (DO) / Español (DO)* o *Spanish / Español*) y haz clic en **Agregar**. Cualquier variante de español sirve: todas usan el mismo archivo de traducción.
2. **Cada usuario:** haz clic en tu avatar (arriba a la derecha) → **Preferencias** → **Idioma** → *Español* y guarda. La página se recarga en español.

Las pantallas principales en cada idioma:

| English | Español |
|---------|---------|
| Board | Tablero |
| Backlog | Backlog |
| Issues | Incidencias |
| Milestones / Version | Hitos / Versión |
| Sprints / Recap | Sprints / Resumen |
| Components | Componentes |
| Sub-tasks | Subtareas |
| Reported by | Reportado por |
| Board Columns | Columnas del tablero |
| New Ticket / My Tickets (📢 icon) | Nuevo ticket / Mis tickets |
| Tickets (Work menu) / IT Support | Tickets / Soporte de TI |

**¿Cambias un texto?** Después de editar una etiqueta o un mensaje en el código, vuelve a exportar la plantilla y añade el texto en español a `es.po`; luego actualiza el módulo:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d ProjectsData --i18n-export=/mnt/extra-addons/dev_addons/i18n/dev_addons.pot \
    --modules=dev_addons --stop-after-init
```

Los textos que falten en `es.po` simplemente se ven en inglés.

---

## Ejecutar las pruebas

Las pruebas se ejecutan en una **base de datos desechable**, así que tus datos reales nunca se tocan:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d test_dev_addons -i dev_addons --test-enable --stop-after-init \
    --test-tags /dev_addons,/project,-/project:TestUi,-/project:TestProjectSharingChatterAccess
```

Esto ejecuta las pruebas de Dev Projects y también las pruebas propias de Proyecto de Odoo, para comprobar que no se ha roto nada en la app Proyecto. Busca esta línea al final:

```
0 failed, 0 error(s) of ... tests
```

`TestProjectSharingChatterAccess` se excluye porque también falla en una instalación de Odoo estándar, y `TestUi` necesita un navegador.

Después, elimina la base de datos de prueba:

```bash
docker exec odoo_dev_database dropdb -U odoo test_dev_addons
```

> En Git Bash para Windows, pon `MSYS_NO_PATHCONV=1` delante del comando `docker compose run`. PowerShell no lo necesita.

---

## Estructura del proyecto

```
odoo_taskvc/
├── docker-compose.yaml        Odoo 17 + PostgreSQL 17
├── config_odoo/odoo.conf      Configuración del servidor Odoo
├── tech_images/               Logos de tecnologías (montada en /tech_images)
├── logs/                      Archivo de log de Odoo (ignorado por git)
└── dev_addons/                El módulo en sí, nombre técnico "dev_addons" (montada en /mnt/extra-addons/dev_addons)
    ├── __manifest__.py
    ├── hooks.py               Pasos de instalación / desinstalación
    ├── data/                  Columnas del tablero por defecto, ajustes
    ├── i18n/                  Traducciones: dev_addons.pot (plantilla), es.po (español)
    ├── migrations/            Pasos de actualización (Histories antiguas → Hitos; resúmenes de sprints antiguos; reportes → tickets numerados)
    ├── models/
    │   ├── project_task.py        Incidencias: tipos, claves, sincronización tablero/Hecho, subtareas, asistente Completar
    │   ├── project_project.py     Proyectos de software, claves, acciones de pantallas
    │   ├── project_task_type.py   Columnas del tablero: categoría de estado, límite WIP
    │   ├── dev_sprint.py          Sprints, el asistente Completar sprint y el resumen del sprint
    │   ├── project_milestone.py   Hitos: versión, progreso, sprints, Completar
    │   ├── dev_module.py          Componentes (partes del software que clasifican incidencias)
    │   ├── dev_report.py          Tickets: enviar, el tablero de tickets, asignar, rechazar, "Sigue sin funcionar"
    │   ├── dev_technology.py      Tecnologías y carga de logos
    │   ├── res_partner.py         Perfiles de desarrollador y códigos de acceso
    │   └── res_config_settings.py Ajustes
    ├── views/                 Tablero, backlog, tickets, hitos, sprints, componentes, formularios, menús, ajustes
    ├── security/              Permisos de acceso (todos pueden enviar tickets y solo ven los suyos)
    ├── static/
    │   ├── description/       Icono de la app
    │   └── src/               El icono 📢 de tickets (report_systray) y el número de tickets en el menú (tickets_counter)
    └── tests/
        ├── test_dev_projects.py   Pruebas de comportamiento
        ├── test_reports.py        Tickets: enviar, el tablero, TI / aplicación, reabrir, quién ve qué
        └── test_screens.py        Todas las pantallas abren; la app Proyecto sigue funcionando
```

`data_generator.py` y `csv/` pertenecen al antiguo módulo `manage`, que se ha eliminado. Dev Projects no los usa.

---

## Desinstalar

Al desinstalar Dev Projects desde *Aplicaciones*, la app Proyecto vuelve a quedar como la entrega Odoo: menús originales y sin filtro por defecto. Tus proyectos y tareas se conservan, subtareas incluidas (son de Odoo). Solo se eliminan los campos de Dev, los sprints y sus resúmenes, los componentes y las tecnologías. Los hitos se conservan, porque pertenecen a la app Proyecto de Odoo.

---

## Licencia

LGPL-3
