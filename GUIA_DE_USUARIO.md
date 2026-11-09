# Dev Projects: Guía de usuario

*English version: [USER_GUIDE.md](USER_GUIDE.md)*

Dev Projects ayuda a tu equipo a planificar y seguir el trabajo de software: qué hay que hacer, quién lo está haciendo y cuánto falta para llegar a los objetivos. Piensa en ello como una lista de tareas compartida por todo el equipo.

No necesitas conocimientos técnicos para usarlo. Esta guía te lo explica todo paso a paso.

> Los nombres de los botones y menús aparecen en español, tal como los verás con Odoo en español (ver [sección 1](#1-abrir-dev-projects-y-ponerlo-en-español)). Si tu pantalla está en inglés, el nombre en inglés va entre paréntesis la primera vez.

---

## Contenido

1. [Abrir Dev Projects y ponerlo en español](#1-abrir-dev-projects-y-ponerlo-en-español)
2. [Palabras que verás](#2-palabras-que-verás)
3. [Cómo encaja todo](#3-cómo-encaja-todo)
4. [Configurar un proyecto (una vez)](#4-configurar-un-proyecto-una-vez)
5. [Agregar trabajo](#5-agregar-trabajo)
6. [Dividir el trabajo en subtareas](#6-dividir-el-trabajo-en-subtareas)
7. [Planificar un sprint](#7-planificar-un-sprint)
8. [Hacer el trabajo: el Tablero](#8-hacer-el-trabajo-el-tablero)
9. [Terminar un sprint y leer su resumen](#9-terminar-un-sprint-y-leer-su-resumen)
10. [Terminar un hito](#10-terminar-un-hito)
11. [Encontrar cosas](#11-encontrar-cosas)
12. [Enviar un ticket (para todos)](#12-enviar-un-ticket-para-todos)
13. [Atender tickets](#13-atender-tickets)
14. [Agregar a un nuevo miembro del equipo](#14-agregar-a-un-nuevo-miembro-del-equipo)
15. [Preguntas frecuentes](#15-preguntas-frecuentes)

---

## 1. Abrir Dev Projects y ponerlo en español

1. Abre la dirección web que te dio tu empresa e inicia sesión con tu correo electrónico y tu contraseña.
2. Haz clic en la app **Proyectos** (*Projects*) de la pantalla de inicio.
3. Arriba verás dos menús: **Proyecto** (*Project*) y **Proyectos Dev** (*Dev Projects*). Usa **Proyectos Dev** para el trabajo de software.

> **¿No eres del equipo de desarrollo?** No verás la app Proyectos, y no la necesitas. Haz clic en el icono 📢 de arriba a la derecha, en cualquier pantalla, para enviar un ticket: un problema, una idea o un pedido de TI (ver sección 12).

**Para ver todo en español:**

1. Haz clic en tu foto o tus iniciales, arriba a la derecha.
2. Haz clic en **Preferencias** (*Preferences*).
3. Cambia el **Idioma** (*Language*) a **Español** y guarda.

La página se recarga en español. Cada persona elige su idioma: tú puedes trabajar en español y un compañero en inglés. Si **Español** no aparece en la lista, pide a un responsable que lo agregue una vez en **Ajustes → Ajustes generales → Idiomas → Agregar idiomas**.

El menú **Proyectos Dev** tiene cuatro partes:

| Menú | Qué contiene |
|---|---|
| **Planificación** (*Planning*) | Proyectos, Hitos, Sprints, Componentes: la visión general |
| **Trabajo** (*Work*) | Tablero, Backlog y Tickets: el trabajo del día a día |
| **Equipo** (*Team*) | Tu perfil de desarrollador, los desarrolladores y las tecnologías que usan |
| **Configuración** (*Configuration*) | Ajustes (solo responsables) |

---

## 2. Palabras que verás

| Palabra | Qué significa | Ejemplo |
|---|---|---|
| **Proyecto** | El producto que están construyendo | *AI glasses* |
| **Incidencia** (*Issue*) | Una pieza de trabajo | *"Agregar un botón de inicio de sesión"* |
| **Clave** (*Key*) | El código corto de la incidencia, como un número de ticket | *AG-12* |
| **Historia** (*Story*) | Algo nuevo que un usuario podrá hacer | *"Los usuarios pueden recuperar su contraseña"* |
| **Tarea** (*Task*) | Un trabajo general | *"Actualizar el logo"* |
| **Error** (*Bug*) | Algo que está roto | *"La app se cierra al tomar una foto"* |
| **Mejora** (*Improvement*) | Mejorar algo que ya funciona | *"Hacer la cámara más rápida"* |
| **Subtarea** (*Sub-task*) | Un paso más pequeño dentro de una incidencia | *"Diseñar el botón"*, *"Programarlo"* |
| **Backlog** | La lista de espera con todo el trabajo aún no empezado | |
| **Sprint** | Un periodo corto de trabajo, normalmente de 1–2 semanas | *Sprint 1* |
| **Resumen** (*Recap*) | El balance de un sprint terminado | *"12 de 15 incidencias terminadas"* |
| **Tablero** (*Board*) | La pantalla con columnas donde avanzas el trabajo | |
| **Ticket** | Un problema, una idea o un pedido de TI que envía alguien de fuera del equipo | *TCK-12 "No puedo imprimir facturas"* |
| **Hito** (*Milestone*) | Un objetivo grande con fecha límite | *"Lanzamiento beta el 1 dic"* |
| **Versión** (*Version*) | El número de versión con el que sale un hito | *1.0.0* |
| **Componente** (*Component*) | Una parte de la app | *Inicio de sesión, Cámara, Ajustes* |
| **Puntos de historia** (*Story points*) | El tamaño aproximado del trabajo (número más alto = más esfuerzo) | *1, 3, 5, 8* |
| **Responsable** (*Assignee*) | La persona que hace el trabajo | |
| **Reportado por** (*Reported by*) | La persona que creó la incidencia | |

---

## 3. Cómo encaja todo

```
Proyecto: AI glasses
├─ Hitos        → ¿A qué objetivo contribuye?   "Lanzamiento beta" (versión 1.0.0)
├─ Sprints      → ¿Cuándo lo hacemos?           "Sprint 1"
└─ Componentes  → ¿Qué parte de la app es?      "Cámara"
```

Cada pieza de trabajo (una **incidencia**) puede llevar las tres etiquetas. Por ejemplo:

> **AG-4 Error: Mensaje de contraseña incorrecta**
> Hito: *Lanzamiento beta* · Sprint: *Sprint 1* · Componente: *Inicio de sesión*

Las incidencias grandes se pueden dividir en **subtareas** más pequeñas (ver sección 6).

**El ciclo habitual:**

**Backlog** (anótalo) → **Sprint** (elige qué hacer ahora) → **Tablero** (hazlo) → **Termina el sprint** (lee el resumen) → repite

---

## 4. Configurar un proyecto (una vez)

Normalmente lo hace un responsable.

1. Ve a **Proyectos Dev → Planificación → Proyectos** y haz clic en **Nuevo**.
2. Escribe el nombre del proyecto y guarda. El proyecto recibe automáticamente una **clave** corta (p. ej. "AI glasses" recibe **AG**) y sus columnas en el **Tablero**.
3. Rellena las pestañas de la parte inferior del proyecto:
   - **Desarrollo:** pega el enlace al código del proyecto (GitHub), si lo tienes.
   - **Componentes:** haz clic en **Agregar línea** y agrega las partes de tu app, p. ej. *Inicio de sesión*, *Cámara*, *Ajustes*.
   - **Hitos:** haz clic en **Agregar línea** y agrega tus objetivos grandes con fecha límite, p. ej. *"Lanzamiento beta"*, para el *1 dic*.

**Ponerle versión a un hito:** abre el hito y escribe su **Versión**, p. ej. *1.0.0*. Solo acepta números de versión, como *1.0*, *1.2.0* o *v2.0.1*. Una palabra sola como "beta" no vale, pero *2.1.0-beta* sí.

---

## 5. Agregar trabajo

Ve a **Proyectos Dev → Trabajo → Backlog**.

1. Haz clic en **Agregar línea**.
2. Escribe un título corto, p. ej. *"El botón de foto no responde"*.
3. Elige el **tipo**: Historia, Tarea, Error o Mejora.
4. Elige el **Componente**: de qué parte de la app se trata.
5. Si quieres, elige quién lo hará (**Responsable**) y su tamaño (**Puntos de historia**).

**El orden importa:** arrastra las líneas arriba y abajo para dejar lo más importante arriba del todo.

**Abrir una incidencia:** al hacer clic en una línea solo la editas ahí mismo. Para ver la incidencia completa (descripción, capturas de pantalla, fecha límite, subtareas), haz clic en **Ver** al final de la línea, a la derecha. **Reportado por** muestra quién la creó; se rellena solo.

---

## 6. Dividir el trabajo en subtareas

Cuando una incidencia es grande, divídela en pasos más pequeños.

1. Abre la incidencia.
2. Ve a su pestaña **Subtareas** (*Sub-tasks*).
3. Haz clic en **Agregar línea** por cada paso, p. ej. *"Diseñar el botón"*, *"Programarlo"*, *"Probarlo"*.

Bueno saberlo:

- Cada subtarea recibe su propia clave (p. ej. **AG-7**) y se puede abrir como cualquier incidencia.
- Las subtareas siempre están en el mismo sprint que su incidencia. Si la incidencia pasa a otro sprint, sus subtareas se van con ella.
- Las subtareas no tienen tarjeta propia en el **Tablero**. En su lugar, la tarjeta de la incidencia muestra cuántas están hechas, p. ej. **☑ 2/5**.
- Las subtareas no tienen puntos de historia: cuenta la incidencia a la que pertenecen.

---

## 7. Planificar un sprint

Un sprint es un periodo corto, normalmente de 1–2 semanas, en el que el equipo se compromete con un conjunto de trabajo.

1. Ve a **Proyectos Dev → Planificación → Sprints** (o a la pestaña **Sprints** de tu proyecto) y haz clic en **Nuevo**.
2. Elige el **Hito** al que contribuye este sprint.
3. Vuelve al **Backlog** y, en cada incidencia que quieras hacer en este sprint, rellena la columna **Sprint**.
4. Cuando el equipo esté listo, abre el sprint y haz clic en **Iniciar sprint**.

Solo puede haber un sprint en curso por proyecto.

---

## 8. Hacer el trabajo: el Tablero

Ve a **Proyectos Dev → Trabajo → Tablero**. Aquí pasarás la mayor parte del tiempo.

El **Tablero** tiene cuatro columnas:

**Por hacer → En curso → En revisión → Hecho**

- Cada columna muestra primero las **tarjetas más importantes**: los errores graves (Críticos o Bloqueantes) arriba del todo, y luego según las estrellas de prioridad. Para subir una tarjeta, dale más estrellas.
- **Arrastra una tarjeta** a la siguiente columna según avance el trabajo.
- Al mover una tarjeta a **En curso** se guarda cuándo empezaste; al moverla a **Hecho**, cuándo terminaste.
- Haz clic en una tarjeta para abrirla, escribir comentarios o adjuntar archivos.
- Para quedarte con una incidencia, ábrela y haz clic en **Asignarme**.
- Las incidencias nuevas creadas en el **Tablero** entran directamente en el sprint en curso.

**Qué muestra el Tablero:** el trabajo del **sprint en curso**, más el trabajo que aún no está planificado en ningún sprint.

---

## 9. Terminar un sprint y leer su resumen

Al final del sprint:

1. Abre el sprint (**Planificación → Sprints**).
2. Haz clic en **Completar sprint**.
3. Elige a dónde va el trabajo sin terminar: al **siguiente sprint** o de vuelta al **Backlog**.
4. Se abre el **resumen** del sprint. Muestra:
   - cuántas incidencias y puntos de historia se terminaron, sobre todo lo que había en el sprint;
   - lo terminado por tipo (p. ej. cuántos errores se corrigieron), por componente y por persona;
   - la lista de incidencias terminadas, y las que quedaron sin terminar con su destino.
5. Escribe unas líneas en el cuadro **Notas del sprint** sobre de qué trató el sprint y haz clic en **Guardar**.

Puedes volver a leer el resumen cuando quieras: abre el sprint terminado y lo primero que verás es su pestaña **Resumen**. Ahí también puedes editar las notas.

Después planifica el siguiente sprint (ver sección 7).

---

## 10. Terminar un hito

Cuando se alcance el objetivo:

1. Abre el proyecto, ve a la pestaña **Hitos** y haz clic en el hito.
2. Haz clic en **Marcar como completado**.

Cada hito muestra una **barra de progreso** para que veas cuánto falta. Si pasa la fecha límite antes de completarlo, se pone en **rojo** y muestra **Atrasado**.

---

## 11. Encontrar cosas

En la parte de arriba del **Tablero** y del **Backlog** hay una **barra de búsqueda**. Haz clic en la flecha pequeña de al lado para ver filtros ya preparados:

| Filtro | Muestra |
|---|---|
| **Asignadas a mí** | Tu propio trabajo |
| **Reportadas por mí** | El trabajo que creaste tú |
| **Errores** | Solo los errores |
| **Abiertas** | Todo lo que no está terminado |
| **Vencidas** | El trabajo que ha pasado su fecha límite |
| **Prioridad alta** | El trabajo importante |
| **Sin componente** / **Sin hito** | El trabajo que aún hay que etiquetar |
| **Archivadas** | El trabajo completado y retirado del Tablero |

También puedes escribir la clave de una incidencia, p. ej. **AG-12**, para encontrarla al momento.

---

## 12. Enviar un ticket (para todos)

No necesitas ser desarrollador para esto. Cualquier persona de la empresa puede enviarle un ticket al equipo (desarrolladores y TI): algo que no funciona, una idea o una pregunta.

1. Haz clic en el icono 📢 de arriba a la derecha (junto a los iconos del chat y del reloj). Está en todas las pantallas.
2. Haz clic en **Nuevo ticket** (*New Ticket*). Se abre una ventana pequeña.
3. Rellena:
   - **Título**: unas pocas palabras, p. ej. *"No puedo imprimir facturas"*.
   - **¿De qué se trata?** (*What's it about?*):
     - **Una aplicación de Odoo**: luego elige la **Aplicación** donde ocurre, p. ej. *Ventas* o *Inventario*. Solo ves las aplicaciones que usas.
     - **Soporte de TI**: tu computadora, impresora, internet, correo o contraseñas.
   - **¿Qué es?**: *Algo no funciona*, *Pedir una función nueva* o *Pregunta*.
   - **¿Qué tan urgente es?**: desde *Puede esperar* hasta *No puedo trabajar*.
   - **Detalles**: si algo no funciona, una nota breve te indica qué escribir: dónde estabas y en qué hiciste clic, qué esperabas y qué pasó en cambio. Puedes pegar capturas de pantalla aquí.
4. Haz clic en **Enviar** (*Send*). Verás "¡Gracias!" y el número de tu ticket, p. ej. **TCK-12**. Menciona ese número si hablas con el equipo sobre él.

**Reportado por** se rellena con tu nombre, para que el equipo sepa quién lo envió.

**Seguimiento:** haz clic en el icono 📢 → **Mis tickets** (*My Tickets*). Cada ticket muestra en qué punto está:

**Esperando revisión → Aceptado → En curso → Hecho**

Si el equipo decide no hacerlo, aparece como **Rechazado** con el motivo. Recibirás un aviso cuando se acepte, se rechace y se termine. También puedes escribirle al equipo en la parte de abajo del ticket.

**¿Sigue sin funcionar?** Durante 7 días después de que un ticket se marque como Hecho, ábrelo y haz clic en **Sigue sin funcionar** (*Still not fixed*). Escribe qué sigue mal y vuelve al equipo.

Solo ves tus propios tickets. Cuando el equipo ya aceptó un ticket, no se puede editar, pero puedes seguir agregando mensajes.

---

## 13. Atender tickets

*Para el equipo (desarrolladores y TI).*

Ve a **Proyectos Dev → Trabajo → Tickets**. El menú muestra cuántos tickets nuevos están esperando, p. ej. **Tickets 3**.

Los tickets tienen su **propio tablero**. Nunca entran en un proyecto, el backlog ni un sprint, así que el trabajo scrum queda aparte.

**Nuevo → Por hacer → En curso → Hecho**

- Los tickets más urgentes aparecen arriba en cada columna. Los **Urgente** y **No puedo trabajar** además avisan a todo el equipo en cuanto llegan.
- **Aceptar** pasa un ticket nuevo a **Por hacer**. **Rechazar** pide un motivo breve y amable, que verá quien lo envió.
- **Iniciar** y **Marcar como hecho** lo avanzan, o simplemente arrastra la tarjeta.
- **Asignado a** muestra quién lo atiende. Haz clic en **Asignarme** para tomarlo. Si inicias un ticket que nadie tiene, queda asignado a ti.
- Cada tarjeta muestra el número del ticket, si es de **TI** o de qué **Aplicación**, qué tan urgente es, quién lo envió y quién lo atiende.
- Filtros: **Nuevo**, **Abiertos**, **Asignados a mí**, **Sin asignar**, **TI**, **Aplicaciones**, **Urgente**. Escribe un número como **TCK-12** para encontrar un ticket.

Para aceptar varios a la vez, márcalos en la lista y usa **Acciones → Aceptar**. ¿Lo rechazaste por error? Ábrelo y haz clic en **Revisar de nuevo**.

Si alguien hace clic en **Sigue sin funcionar**, el ticket vuelve a **Por hacer** con su comentario, y a quien lo atendía se le avisa.

---


## 14. Agregar a un nuevo miembro del equipo

*Para responsables.*

Para asignar trabajo a alguien, necesita un acceso (usuario):

1. Ve a **Proyectos Dev → Equipo → Desarrolladores** y abre (o crea) a la persona.
2. Comprueba que su **correo electrónico** esté rellenado y guarda.
3. Haz clic en **Crear usuario** en el mensaje azul.
4. Ya podrá iniciar sesión con su correo. Envíale una invitación desde **Ajustes → Usuarios** para que elija su contraseña, o pónsela tú.

Cada desarrollador tiene también un **código de acceso**: 8 números seguidos de letras, p. ej. **12345678A**. Una vez guardado, no se puede cambiar.

---

## 15. Preguntas frecuentes

**Creé una incidencia pero no la veo en el Tablero.**
Seguramente está en un sprint que aún no ha empezado. El **Tablero** solo muestra el sprint *en curso*. Pide a tu responsable que haga clic en **Iniciar sprint**, o busca la incidencia en el **Backlog**.

**Agregué una subtarea pero no está en el Tablero.**
Es normal: las subtareas viven dentro de su incidencia. Abre la incidencia y mira su pestaña **Subtareas**.

**Un mensaje dijo que mi incidencia "fue al backlog".**
No había ningún sprint en curso, así que la incidencia se guardó en el Backlog. No se ha perdido nada.

**Mi tarjeta desapareció después de hacer clic en "Completar".**
**Completar** marca el trabajo como hecho y lo quita del **Tablero**. Para verla otra vez, usa el filtro **Archivadas**.

**No puedo mover una tarjeta a una columna.**
Esa columna tiene un límite de tarjetas a la vez. Termina primero algo de esa columna, o pide a un responsable que suba el límite.

**El hito no acepta mi versión.**
El cuadro **Versión** solo acepta números de versión, como *1.0*, *1.2.0* o *v2.0.1*.

**No puedo elegir a alguien como Responsable.**
Todavía no tiene acceso. Un responsable puede crearle uno (ver sección 14).

**¿Por qué los tickets no aparecen en el backlog?**
Es a propósito. Los tickets son pedidos de personas de fuera del equipo y tienen su propio tablero en **Trabajo → Tickets**. El backlog y los sprints son solo para el trabajo del propio equipo.

**Nuestra persona de TI no ve el menú Tickets.**
Necesita permisos de usuario de Proyecto, como los desarrolladores. Un responsable puede agregarlos en **Ajustes → Usuarios** (Proyecto: Usuario).

**¿Qué es el menú "Proyecto" que está junto a "Proyectos Dev"?**
Es para los otros proyectos de la empresa que no son de software. Para el trabajo de software, usa **Proyectos Dev**.

**Hice clic en algo por error.**
- Marcado como hecho por error → abre la incidencia y haz clic en **Reabrir**.
- Moviste una tarjeta a la columna equivocada → simplemente arrástrala de vuelta.

---

*¿Necesitas más ayuda? Pregunta a tu responsable de proyecto.*
