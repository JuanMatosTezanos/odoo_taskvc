# Dev Projects: Guía de usuario

*English version: [USER_GUIDE.md](USER_GUIDE.md)*

Dev Projects ayuda a tu equipo a planificar y seguir el trabajo de software: qué hay que hacer, quién lo está haciendo y cuánto falta para llegar a los objetivos. Piensa en ello como una lista de tareas compartida por todo el equipo.

No necesitas conocimientos técnicos para usarlo. Esta guía te lo explica todo paso a paso.

---

## Contenido

1. [Abrir Dev Projects](#1-abrir-dev-projects)
2. [Palabras que verás](#2-palabras-que-verás)
3. [Cómo encaja todo](#3-cómo-encaja-todo)
4. [Configurar un proyecto (una vez)](#4-configurar-un-proyecto-una-vez)
5. [Añadir trabajo](#5-añadir-trabajo)
6. [Planificar un sprint](#6-planificar-un-sprint)
7. [Hacer el trabajo: el Board](#7-hacer-el-trabajo-el-board)
8. [Terminar un sprint](#8-terminar-un-sprint)
9. [Terminar un milestone](#9-terminar-un-milestone)
10. [Encontrar cosas](#10-encontrar-cosas)
11. [Añadir a un nuevo miembro del equipo](#11-añadir-a-un-nuevo-miembro-del-equipo)
12. [Preguntas frecuentes](#12-preguntas-frecuentes)

> Los nombres de los botones y menús aparecen en inglés, tal como los verás en la pantalla.

---

## 1. Abrir Dev Projects

1. Abre la dirección web que te dio tu empresa e inicia sesión con tu email y contraseña.
2. Haz clic en la app **Projects** de la pantalla de inicio.
3. Arriba verás dos menús: **Project** y **Dev Projects**. Usa **Dev Projects** para el trabajo de software.

El menú **Dev Projects** tiene cuatro partes:

| Menú | Qué contiene |
|---|---|
| **Planning** | Projects, Milestones, Sprints, Modules: la visión general |
| **Work** | Board y Backlog: el trabajo del día a día |
| **Team** | Tu perfil de desarrollador, los desarrolladores y las tecnologías que usáis |
| **Configuration** | Ajustes (solo responsables) |

---

## 2. Palabras que verás

| Palabra | Qué significa | Ejemplo |
|---|---|---|
| **Project** (proyecto) | El producto que estáis construyendo | *AI glasses* |
| **Issue** (incidencia) | Una pieza de trabajo | *"Añadir un botón de inicio de sesión"* |
| **Key** (clave) | El código corto de la incidencia, como un número de ticket | *AG-12* |
| **Story** | Algo nuevo que un usuario podrá hacer | *"Los usuarios pueden recuperar su contraseña"* |
| **Task** | Un trabajo general | *"Actualizar el logo"* |
| **Bug** | Algo que está roto | *"La app se cierra al hacer una foto"* |
| **Improvement** | Mejorar algo que ya funciona | *"Hacer la cámara más rápida"* |
| **Backlog** | La lista de espera con todo el trabajo aún no empezado | |
| **Sprint** | Un periodo corto de trabajo, normalmente de 1–2 semanas | *Sprint 1* |
| **Board** (tablero) | La pantalla con columnas donde avanzas el trabajo | |
| **Milestone** (hito) | Un objetivo grande con fecha límite | *"Lanzamiento beta el 1 dic"* |
| **Module** (módulo) | Una parte de la app | *Login, Cámara, Ajustes* |
| **Story points** | El tamaño aproximado del trabajo (número más alto = más esfuerzo) | *1, 3, 5, 8* |
| **Assignee** (responsable) | La persona que hace el trabajo | |
| **Reporter** (informador) | La persona que creó la incidencia | |

---

## 3. Cómo encaja todo

```
Proyecto: AI glasses
├─ Milestones → ¿A qué objetivo contribuye?   "Lanzamiento beta"
├─ Sprints    → ¿Cuándo lo hacemos?           "Sprint 1"
└─ Modules    → ¿Qué parte de la app es?      "Cámara"
```

Cada pieza de trabajo (una **incidencia**) puede llevar las tres etiquetas. Por ejemplo:

> **AG-4 Bug: Mensaje de contraseña incorrecta**
> Milestone: *Lanzamiento beta* · Sprint: *Sprint 1* · Module: *Login*

**El ciclo habitual:**

**Backlog** (anótalo) → **Sprint** (elige qué hacer ahora) → **Board** (hazlo) → **Termina el sprint** → repite

---

## 4. Configurar un proyecto (una vez)

Normalmente lo hace un responsable.

1. Ve a **Dev Projects → Planning → Projects** y haz clic en **New**.
2. Escribe el nombre del proyecto y guarda. El proyecto recibe automáticamente una **clave** corta (p. ej. "AI glasses" recibe **AG**) y un tablero.
3. Rellena las pestañas de la parte inferior del proyecto:
   - **Development:** pega el enlace al código del proyecto (GitHub), si lo tienes.
   - **Modules:** haz clic en **Add a line** y añade las partes de tu app, p. ej. *Login*, *Cámara*, *Ajustes*.
   - **Milestones:** haz clic en **Add a line** y añade tus objetivos grandes con fecha límite, p. ej. *"Lanzamiento beta"*, para el *1 dic*.

---

## 5. Añadir trabajo

Ve a **Dev Projects → Work → Backlog**.

1. Haz clic en **Add a line**.
2. Escribe un título corto, p. ej. *"El botón de foto no responde"*.
3. Elige el **tipo**: Story, Task, Bug o Improvement.
4. Elige el **Module**: de qué parte de la app se trata.
5. Si quieres, elige quién lo hará (**Assignee**) y su tamaño (**Story Points**).

**El orden importa:** arrastra las líneas arriba y abajo para dejar lo más importante arriba del todo.

Para añadir más detalles (una descripción, capturas de pantalla, una fecha límite), haz clic en la incidencia para abrirla.

---

## 6. Planificar un sprint

Un sprint es un periodo corto, normalmente de 1–2 semanas, en el que el equipo se compromete con un conjunto de trabajo.

1. Ve a **Dev Projects → Planning → Sprints** (o a la pestaña **Sprints** de tu proyecto) y haz clic en **New**.
2. Elige el **Milestone** al que contribuye este sprint.
3. Vuelve al **Backlog** y, en cada incidencia que quieras hacer en este sprint, rellena la columna **Sprint**.
4. Cuando el equipo esté listo, abre el sprint y haz clic en **Start Sprint**.

Solo puede haber un sprint en marcha por proyecto.

---

## 7. Hacer el trabajo: el Board

Ve a **Dev Projects → Work → Board**. Aquí pasarás la mayor parte del tiempo.

El Board tiene cuatro columnas:

**To Do → In Progress → In Review → Done**

(Por hacer → En curso → En revisión → Hecho)

- **Arrastra una tarjeta** a la siguiente columna según avance el trabajo.
- Al mover una tarjeta a **In Progress** se guarda cuándo empezaste; al moverla a **Done**, cuándo terminaste.
- Haz clic en una tarjeta para abrirla, escribir comentarios o adjuntar archivos.
- Para quedarte con una incidencia, ábrela y haz clic en **Assign to Me**.
- Las incidencias nuevas creadas en el Board entran directamente en el sprint en marcha.

**Qué muestra el Board:** el trabajo del **sprint en marcha**, más el trabajo que aún no está planificado en ningún sprint.

---

## 8. Terminar un sprint

Al final del sprint:

1. Abre el sprint (**Planning → Sprints**).
2. Haz clic en **Complete Sprint**.
3. Elige a dónde va el trabajo sin terminar: al **siguiente sprint** o de vuelta al **Backlog**.

Después planifica el siguiente sprint (ver sección 6).

---

## 9. Terminar un milestone

Cuando se alcance el objetivo:

1. Abre el proyecto, ve a la pestaña **Milestones** y haz clic en el milestone.
2. Haz clic en **Mark as Complete**.

Cada milestone muestra una **barra de progreso** para que veas cuánto falta. Si pasa la fecha límite antes de completarlo, se pone en **rojo** y muestra **Late** (con retraso).

---

## 10. Encontrar cosas

En la parte de arriba del Board y del Backlog hay una **barra de búsqueda**. Haz clic en la flecha pequeña de al lado para ver filtros ya preparados:

| Filtro | Muestra |
|---|---|
| **Assigned to Me** | Tu propio trabajo |
| **Bugs** | Solo los bugs |
| **Open** | Todo lo que no está terminado |
| **Overdue** | El trabajo que ha pasado su fecha límite |
| **High Priority** | El trabajo importante |
| **No Module** / **No Milestone** | El trabajo que aún hay que etiquetar |
| **Archived** | El trabajo completado y retirado del Board |

También puedes escribir la clave de una incidencia, p. ej. **AG-12**, para encontrarla al momento.

---

## 11. Añadir a un nuevo miembro del equipo

*Para responsables.*

Para asignar trabajo a alguien, necesita un acceso (usuario):

1. Ve a **Dev Projects → Team → Developers** y abre (o crea) a la persona.
2. Comprueba que su **email** esté rellenado y guarda.
3. Haz clic en **Create User** en el mensaje azul.
4. Ya podrá iniciar sesión con su email. Envíale una invitación desde **Settings → Users** para que elija su contraseña, o pónsela tú.

Cada desarrollador tiene también un **código de acceso**: 8 números seguidos de letras, p. ej. **12345678A**. Una vez guardado, no se puede cambiar.

---

## 12. Preguntas frecuentes

**He creado una incidencia pero no la veo en el Board.**
Seguramente está en un sprint que aún no ha empezado. El Board solo muestra el sprint *en marcha*. Pide a tu responsable que haga clic en **Start Sprint**, o busca la incidencia en el **Backlog**.

**Un mensaje dijo que mi incidencia "went to the backlog" (fue al backlog).**
No había ningún sprint en marcha, así que la incidencia se guardó en el Backlog. No se ha perdido nada.

**Mi tarjeta desapareció después de hacer clic en "Complete".**
**Complete** marca el trabajo como hecho y lo quita del Board. Para verla otra vez, usa el filtro **Archived**.

**No puedo mover una tarjeta a una columna.**
Esa columna tiene un límite de tarjetas a la vez. Termina primero algo de esa columna, o pide a un responsable que suba el límite.

**No puedo elegir a alguien como Assignee.**
Todavía no tiene acceso. Un responsable puede crearle uno (ver sección 11).

**¿Qué es el menú "Project" que está junto a "Dev Projects"?**
Es para los otros proyectos de la empresa que no son de software. Para el trabajo de software, usa **Dev Projects**.

**He hecho clic en algo por error.**
- Marcado como hecho por error → abre la incidencia y haz clic en **Reopen**.
- Moviste una tarjeta a la columna equivocada → simplemente arrástrala de vuelta.

---

*¿Necesitas más ayuda? Pregunta a tu responsable de proyecto.*
