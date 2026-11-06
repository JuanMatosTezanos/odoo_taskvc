# Dev Projects para Odoo 17

Gestión de proyectos de software al estilo Jira, construida sobre la app **Project** de Odoo.

> **¿Solo vas a usar la app?** Lee la [Guía de usuario](GUIA_DE_USUARIO.md) en lenguaje sencillo ([User Guide in English](USER_GUIDE.md)). Este README es para quienes la instalan y la mantienen.

Dev Projects añade claves de incidencia (`WEB-1`, `WEB-2`…), tipos de incidencia, un tablero con límites WIP, un backlog ordenado, sprints que se inician y se completan a mano, milestones (hitos), módulos, tecnologías y perfiles de desarrollador. Trabaja sobre **los mismos proyectos y tareas** que la app Project. Una incidencia es una tarea normal de Odoo con campos extra, así que puedes cambiar entre las dos apps en cualquier momento.

---

## Contenido

- [Funcionalidades](#funcionalidades)
- [Cómo encaja con la app Project](#cómo-encaja-con-la-app-project)
- [Primeros pasos](#primeros-pasos)
- [Flujo de trabajo diario](#flujo-de-trabajo-diario)
- [Configuración](#configuración)
- [Ejecutar las pruebas](#ejecutar-las-pruebas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desinstalar](#desinstalar)

---

## Funcionalidades

**Incidencias**
- Tipos: Story, Task, Bug, Improvement.
- Una clave por proyecto, p. ej. `AG-1`, `AG-2`. Se sugiere a partir del nombre del proyecto ("AI glasses" → `AG`) y se puede buscar por ella.
- Puntos de historia, una prioridad de 4 niveles (Normal, Important, High, Critical) y una severidad para los bugs.
- Un **responsable** (que también se añade a los asignados de la tarea en Odoo) y un **informador**.
- Fechas de inicio y fin que se rellenan automáticamente a medida que la incidencia avanza por el tablero.
- Pausar/reanudar, avisos de vencimiento y **Complete**: marcarla como hecha y después archivarla o eliminarla.

**Tablero (Board)**
- Las columnas son etapas de proyecto de Odoo, cada una con una categoría de estado: To Do, In Progress, In Review o Done.
- Mover una tarjeta a una columna Done marca la tarea como hecha también en la app Project, y sacarla de ahí la reabre.
- **Límite WIP** opcional por columna, contado por proyecto y sprint. Las columnas Done nunca tienen límite.
- Muestra el **trabajo actual**: el sprint en curso más las incidencias que no están en ningún sprint.

**Backlog y sprints**
- Backlog agrupado por sprint. Arrastra para ordenar las incidencias y elige un sprint para planificarlas.
- Los sprints se inician y se completan a mano, como en Jira. Solo puede haber un sprint en curso por proyecto.
- Al completar un sprint, las incidencias sin terminar pasan al siguiente sprint o vuelven al backlog.
- Progreso del sprint, puntos planificados y puntos completados.

**Milestones (hitos)**
- Un milestone es un objetivo con fecha límite, p. ej. *"Login completo — 20 nov"*. Agrupa **sprints** e **incidencias**:
  ```
  Proyecto: AI glasses
  └─ Milestone: Login completo (vence 20 nov)   ███░░ 60%
     ├─ Sprint 1 → AG-1 Story: formulario de login, AG-2 Bug: mensaje de contraseña incorrecta
     └─ Sprint 2 → AG-3 Improvement: login con Google
  ```
- Vincula un sprint a un milestone y todas las incidencias de ese sprint se unen al milestone automáticamente. También se puede asignar un milestone directamente a una incidencia.
- Cada milestone muestra su progreso (incidencias y puntos de historia completados), bugs y tecnologías usadas. Se pone en rojo con una cinta **Late** al pasar su fecha límite, y tiene un botón **Mark as Complete**.
- Son los milestones propios de Odoo, así que la app Project muestra los mismos.

**Proyectos**
- Un enlace **GitHub Repository** en cada proyecto de software.
- El formulario del proyecto tiene las pestañas **Development | Milestones | Sprints | Modules | Description | Settings**. Milestones, Sprints y Modules solo aparecen en los proyectos de software.
- Los proyectos de software llaman a sus tareas **Issues** y ocultan los campos "Name of the Tasks" y Tags de Odoo. El botón **Tasks** de Odoo se sustituye por **Open Issues**.

**Módulos (Modules)**
- Los módulos son las partes de tu software, p. ej. *Login*, *Payments*, *Camera*. Cada proyecto tiene su propia lista.
- Elige uno en el campo **Module** de una incidencia (debajo de Dev Priority). Si escribes un nombre nuevo, te ofrece crearlo en el momento.
- Cada módulo tiene un **Lead** (responsable) opcional y muestra sus incidencias, incidencias abiertas, bugs abiertos y tecnologías usadas. Las tarjetas del Board, las listas de incidencias y el Backlog muestran el módulo, y puedes filtrar o agrupar por él.
- Al duplicar un proyecto también se copian sus módulos.

**Tecnologías y desarrolladores**
- Las tecnologías obtienen su logo automáticamente de una carpeta de imágenes (`Docker` → `Docker.png`).
- Perfiles de desarrollador en los contactos:
  - Un código de acceso: 8 dígitos seguidos de letras, p. ej. `12345678A`. Debe ser único y no se puede cambiar una vez guardado.
  - Las tecnologías que conoce el desarrollador.
  - Una etiqueta "Devs", que se añade automáticamente.
  - Un botón **Create User** que da al desarrollador un acceso a Odoo (su email), para poder asignarle incidencias. Vincula el acceso al mismo contacto, así que el perfil se conserva.

---

## Cómo encaja con la app Project

Tras la instalación, la pantalla de inicio muestra una sola app **Projects** con dos menús:

```
Projects  |  Project ▾          |  Dev Projects ▾
          |  Menús propios de   |  Planning: Projects, Milestones, Sprints, Modules
          |  Odoo, sin cambios  |  Work:     Board, Backlog
          |                     |  Team:     My Developer Profile, Developers, Technologies
          |                     |  Configuration
```

- Los **proyectos de software** tienen marcada la casilla *Software Project*. Los proyectos creados desde Dev Projects la tienen marcada automáticamente. Solo estos aparecen en Dev Projects y reciben claves, columnas de tablero y el comportamiento de Dev.
- Los **proyectos normales** (marketing, oficina, etc.) se comportan exactamente como en Odoo estándar.
- La app Project oculta por defecto los proyectos de software con un filtro **"Hide Software Projects"**. Es un filtro de búsqueda normal, así que al quitarlo se ve todo.
- Para pasar un proyecto existente a Dev Projects, marca *Software Project* en él. Recibe una clave y columnas de tablero, y sus tareas existentes se numeran.

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

1. Ve a **Apps**.
2. Quita el filtro "Apps" y busca **Dev Projects**.
3. Haz clic en **Activate**.

La app **Project** se instala automáticamente si no la tienes.

### Después de cambiar el código

- **Cambios en Python:** reinicia el contenedor web con `docker restart odoo_dev_web`.
- **Cambios en vistas/XML o en campos:** actualiza el módulo, desde *Apps → Dev Projects → Upgrade* o desde la línea de comandos:

  ```bash
  docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
      -d ProjectsData -u dev_projects --stop-after-init
  docker restart odoo_dev_web
  ```

---

## Flujo de trabajo diario

**En una línea:** configura Modules y Milestones → escribe incidencias en el **Backlog** → planifica e **inicia** un sprint → arrastra tarjetas en el **Board** → **Complete Sprint** → repite → **marca el milestone como completo**.

Cómo encajan las piezas:

```
Proyecto: AI glasses
├─ Milestones  → ¿POR QUÉ / qué objetivo?   "Login completo", "Lanzamiento beta"
├─ Sprints     → ¿CUÁNDO se hace?           "Sprint 1", "Sprint 2"
└─ Modules     → ¿QUÉ parte es?             "Login", "Camera", "UI"
```

Una incidencia puede tener las tres, p. ej. **AG-4 Bug: Mensaje de contraseña incorrecta**, con Milestone *Login completo*, Sprint *Sprint 1* y Module *Login*.

### 1. Configura el proyecto (una vez)
*Dev Projects → Planning → Projects → New*. Escribe el nombre y guarda; recibe una clave (p. ej. `AG`) y columnas de tablero. Después rellena las pestañas:
- **Development:** revisa la clave y pega el enlace **GitHub Repository**.
- **Modules:** añade las partes de tu app con **Add a line**, p. ej. *Login, Camera, UI*.
- **Milestones:** añade tus objetivos grandes con fecha límite, p. ej. *"Lanzamiento beta — 1 dic"*.

### 2. Anota el trabajo (en cualquier momento)
*Work → **Backlog***
- **Add a line** por cada cosa que hacer y elige su tipo: Story, Task, Bug o Improvement.
- Asigna su **Module**.
- Arrastra las líneas para dejar las más importantes arriba.

### 3. Planifica un sprint (cada 1–2 semanas)
En la pestaña **Sprints** del proyecto, o en *Planning → Sprints*:
1. Crea un sprint y elige el **Milestone** al que contribuye.
2. En el **Backlog**, rellena la columna **Sprint** en las incidencias que vas a hacer. Se unen automáticamente al milestone del sprint.
3. Abre el sprint y haz clic en **Start Sprint**.

### 4. Haz el trabajo (cada día)
*Work → **Board***
- Arrastra tarjetas: **To Do → In Progress → In Review → Done**.
- Las incidencias nuevas creadas aquí entran directamente en el sprint en curso.

### 5. Termina el sprint
Abre el sprint y haz clic en **Complete Sprint**. Las incidencias sin terminar pasan al siguiente sprint o vuelven al backlog. Luego repite desde el paso 3.

### 6. Termina el milestone
Cuando se alcance su objetivo, ábrelo (pestaña **Milestones** del proyecto) y haz clic en **Mark as Complete**.

**Botones que puedes ignorar al principio**
- **Start / Send to Review / Mark as Done** en una incidencia hacen lo mismo que arrastrar su tarjeta.
- **Pause / Resume** y **Assign to Me** son atajos pequeños.
- **Complete** en una incidencia la marca como hecha *y* quita la tarjeta del tablero (archivar o eliminar). Úsalo solo cuando quieras que desaparezca.
- **Reopen** es solo para algo marcado como hecho por error.
- El menú **Project** es la app normal de Odoo para proyectos que no son de software. Puedes trabajar solo en **Dev Projects**.

> **¿Por qué no veo las incidencias de mi sprint en el Board?**
> El Board muestra el sprint *en curso* más las incidencias que no están en ningún sprint. Las incidencias de un sprint que no se ha iniciado quedan ocultas hasta que haces clic en **Start Sprint**. Para verlas antes, usa el botón **Issues** del sprint o quita el filtro "Current Work".
>
> Si creas una incidencia en el Board sin ningún sprint en curso, va al backlog y una breve notificación te lo indica.

---

## Configuración

**Settings → Project → Dev Projects**

| Ajuste | Por defecto | Qué hace |
|--------|-------------|----------|
| Technology Logo Folder | `/tech_images` | Carpeta donde se buscan los logos `<Nombre de tecnología>.png` |
| Default Sprint Length (days) | 14 | Duración de los sprints nuevos |
| Default Board Columns for New Software Projects | Activado | Da a los proyectos de software nuevos las cuatro columnas por defecto |

**Dev Projects → Configuration → Board Columns**: renombra, reordena o añade columnas, y define la *Status Category* y el *WIP Limit* de cada columna (0 = sin límite).

**Logos de tecnologías**: pon archivos PNG en [`tech_images/`](tech_images/). El nombre del archivo debe coincidir con el nombre de la tecnología, sin importar mayúsculas o minúsculas. La carpeta se monta en solo lectura dentro del contenedor en `/tech_images`.

---

## Ejecutar las pruebas

Las pruebas se ejecutan en una **base de datos desechable**, así que tus datos reales nunca se tocan:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d test_dev_projects -i dev_projects --test-enable --stop-after-init \
    --test-tags /dev_projects,/project,-/project:TestUi,-/project:TestProjectSharingChatterAccess
```

Esto ejecuta las pruebas de Dev Projects y también las pruebas propias de Project de Odoo, para comprobar que no se ha roto nada en la app Project. Busca esta línea al final:

```
0 failed, 0 error(s) of ... tests
```

`TestProjectSharingChatterAccess` se excluye porque también falla en una instalación de Odoo estándar, y `TestUi` necesita un navegador.

Después, elimina la base de datos de prueba:

```bash
docker exec odoo_dev_database dropdb -U odoo test_dev_projects
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
└── dev_addons/                Addons propios (montada en /mnt/extra-addons)
    └── dev_projects/
        ├── __manifest__.py
        ├── hooks.py           Pasos de instalación / desinstalación
        ├── data/              Columnas de tablero por defecto, ajustes
        ├── migrations/        Pasos de actualización (p. ej. convertir las antiguas Histories en Milestones)
        ├── models/
        │   ├── project_task.py        Incidencias: tipos, claves, sincronización tablero/Done, asistente Complete
        │   ├── project_project.py     Proyectos de software, claves, acciones de pantallas
        │   ├── project_task_type.py   Columnas del tablero: categoría de estado, límite WIP
        │   ├── dev_sprint.py          Sprints y el asistente Complete Sprint
        │   ├── project_milestone.py   Milestones: progreso, sprints, Complete
        │   ├── dev_module.py          Módulos: partes del software que clasifican incidencias
        │   ├── dev_technology.py      Tecnologías y carga de logos
        │   ├── res_partner.py         Perfiles de desarrollador y códigos de acceso
        │   └── res_config_settings.py Ajustes
        ├── views/             Tablero, backlog, milestones, sprints, módulos, formularios, menús, ajustes
        ├── security/          Permisos de acceso
        └── tests/
            ├── test_dev_projects.py   Pruebas de comportamiento
            └── test_screens.py        Todas las pantallas abren; la app Project sigue funcionando
```

`data_generator.py` y `csv/` pertenecen al antiguo módulo `manage`, que se ha eliminado. Dev Projects no los usa.

---

## Desinstalar

Al desinstalar Dev Projects desde *Apps*, la app Project vuelve a quedar como la entrega Odoo: menús originales y sin filtro por defecto. Tus proyectos y tareas se conservan. Solo se eliminan los campos de Dev, los sprints, los módulos y las tecnologías. Los milestones se conservan, porque pertenecen a la app Project de Odoo.

---

## Licencia

LGPL-3
