
[README -.md](https://github.com/user-attachments/files/34446706/README.-.Copy.md)
# Dev Projects for Odoo 17

Jira-style software project management built on top of Odoo's own **Project** app.

> **Just using the app?** Read the plain-language [User Guide](USER_GUIDE.md) ([Guía de usuario en español](GUIA_DE_USUARIO.md)). This README is for the people who install and maintain it.

Dev Projects adds issue keys (`WEB-1`, `WEB-2`…), issue types, sub-tasks, a **Board** with WIP limits, a ranked backlog, sprints you start and complete by hand (with a recap of each one), milestones with versions, components, technologies and developer profiles. A **report icon** (📢) in the top bar lets anyone in the company send problems and ideas to the dev team. It works on the **same projects and tasks** as the Project app. An issue is a normal Odoo task with extra fields, so you can switch between the two apps at any time. The whole module is available in **English and Spanish**.

---

## Contents

- [Features](#features)
- [How it fits with the Project app](#how-it-fits-with-the-project-app)
- [Getting started](#getting-started)
- [Day-to-day workflow](#day-to-day-workflow)
- [Configuration](#configuration)
- [Languages (English / Spanish)](#languages-english--spanish)
- [Running the tests](#running-the-tests)
- [Project structure](#project-structure)
- [Uninstalling](#uninstalling)

---

## Features

**Issues**
- Types: Story, Task, Bug, Improvement.
- A key per project, e.g. `AG-1`, `AG-2`. It's suggested from the project name ("AI glasses" → `AG`), and you can search by it.
- Story points, a 4-level priority (Normal, Important, High, Critical) and a severity for bugs.
- One **assignee** (also added to the task's assignees in Odoo) and a **Reported by** (who created it).
- Start/finish dates filled in automatically as the issue moves across the board.
- Pause/resume, overdue warnings, and **Complete**: mark it done, then archive or delete it.

**Sub-tasks**
- Split an issue into smaller steps in its **Sub-tasks** tab. They're listed right under the parent issue.
- Each sub-task gets its own key (e.g. `AG-7`), and follows its parent's sprint. It also takes the parent's component if it has none, and follows the parent when that component changes (unless it was given another one on purpose).
- Sub-tasks don't get their own card on the **Board** or a row in the Backlog. The parent's card shows a counter instead, e.g. **☑ 2/5** (sub-tasks done / total), and lists show "(2/5 sub-tasks)" next to the name.
- They don't count on their own in sprint, milestone, component and project numbers, and they don't use a WIP slot: the parent counts. So they have no story points either.

**Board**
- Columns are Odoo project stages, each with a status category: To Do, In Progress, In Review or Done.
- Moving a card to a Done column marks the task done in the Project app too, and moving it out reopens it.
- Optional **WIP limit** per column, counted per project and sprint. Done columns are never limited.
- Shows **current work**: the running sprint plus issues not in any sprint.
- **Most important first** in each column: Critical/Blocker bugs, then by Dev Priority (Critical → High → Important → Normal), then the Backlog order.

**Backlog and sprints**
- Backlog grouped by sprint. Drag to rank issues, and pick a sprint to plan them.
- Sprints are started and completed by hand, like in Jira. Only one sprint per project can run at a time.
- When you complete a sprint, unfinished issues move to the next sprint or back to the backlog.
- Sprint progress, planned points and done points.

**Sprint recap**
- Completing a sprint opens its **recap**:
  - issues and story points finished, out of what was in the sprint at the end;
  - what was finished per type (stories, bugs fixed…), per component and per person;
  - the finished issues, and the unfinished ones with where they went (next sprint or backlog);
  - a **Sprint Summary** box where the team writes what the sprint was about.
- The recap is saved on the sprint. A closed sprint opens on its **Recap** tab, so you can read it or edit the summary later.
- It's a snapshot taken at completion, so it doesn't change when the issues change afterwards.

**Milestones**
- A milestone is a goal with a deadline, e.g. *"Login complete — Nov 20"*. It groups **sprints** and **issues**:
  ```
  Project: AI glasses
  └─ Milestone: Login complete (v1.2.0, due Nov 20)   ███░░ 60%
     ├─ Sprint 1 → AG-1 Story: login form, AG-2 Bug: wrong password message
     └─ Sprint 2 → AG-3 Improvement: Google login
  ```
- An optional **Version** per milestone, e.g. `1.2.0`. It only accepts version numbers: `1.0`, `1.2.0`, `v2.0.1`, or with a tag like `2.1.0-beta`.
- Link a sprint to a milestone, and every issue in that sprint joins the milestone automatically. An issue can also be given a milestone directly.
- Each milestone shows its progress (issues and story points done), bugs and technologies used. It turns red with a **Late** ribbon after its deadline, and has a **Mark as Complete** button.
- These are Odoo's own milestones, so the Project app shows the same ones.

**Projects**
- A **GitHub Repository** link on each software project.
- The project form has the tabs **Development | Milestones | Sprints | Components | Description | Settings**. Milestones, Sprints and Components only appear on software projects.
- Software projects call their tasks **Issues**, and hide Odoo's "Name of the Tasks" and Tags fields. Odoo's **Tasks** button is replaced by **Open Issues**, and the **Board** button opens the board.

**Components**
- Components are the parts of your software, e.g. *Login*, *Payments*, *Camera*. Each project has its own list.
- Pick one in the **Component** field of an issue (under Dev Priority). Typing a new name offers to create it on the spot.
- Each component has an optional **Lead** and shows its issues, open issues, open bugs and technologies used. The cards on the Board, issue lists and Backlog show the component, and you can filter or group by it.
- Duplicating a project copies its components too.
- In the code, components are still called modules (model `dev.module`, field `dev_module_id`), because they were named that first. Only the labels changed, so no data had to move.

**Technologies and developers**
- Technologies get their logo automatically from an image folder (`Docker` → `Docker.png`).
- Developer profiles on contacts:
  - An access code: 8 digits followed by letters, e.g. `12345678A`. It must be unique and can't be changed once saved.
  - Technologies the developer knows.
  - A "Devs" tag, added automatically.
  - A **Create User** button that gives the developer an Odoo login (their email), so issues can be assigned to them. It links the login to the same contact, so the profile stays.

**Reports (for people outside the dev team)**
- A 📢 icon in the top bar, next to chat and activities, on every screen and for every internal user. People without Project rights don't need (or see) the Projects app.
- The icon's menu has **New Report** and **My Reports**.
- **New Report** opens a pop-up form:
  - *Reported by* (filled in)
  - **App**: the Odoo app where it happens, e.g. Sales. Required, and it only lists the apps that person can open.
  - *What is it?*: Something's broken / Request a feature / Question
  - Title and details (screenshots can be pasted in)
  - *How urgent is it?*: It can wait / Normal / Urgent / I can't work
  - **Send** saves it and says thanks.
- **My Reports** lists what you sent and where it stands: *Waiting for review → Accepted → Being worked on → Done*, or *Declined* with the reason. Reporters only see their own reports.
- The dev team reviews them in **Dev Projects → Work → Reports**:
  - **Accept** asks which project's Backlog gets the issue. It's pre-filled when there's only one software project, or with the project last used for the same app. The issue goes in outside any sprint, with:
    - the reporter as *Reported by*
    - the details, screenshots and app copied over
    - type from the report: *Something's broken* → Bug, *Request a feature* → Story, *Question* → Task
    - priority from urgency: *Urgent* → High, *I can't work* → Critical (and Blocker severity for bugs)
  - **Decline** asks for a reason, which the reporter sees. **Review Again** puts a declined report back in the queue.
  - Select several reports in the list and use **Actions → Accept** to accept them at once.
- The reporter follows the report and is notified when it's accepted or declined, and once when its issue is done. The report also shows the issue key and live status.

---

## How it fits with the Project app

After installing, the home screen shows one **Projects** app (for the dev team) with two menus. Everyone else uses the 📢 report icon in the top bar (see [Features](#features)).

```
Projects  |  Project ▾          |  Dev Projects ▾
          |  Odoo's own menus,  |  Planning: Projects, Milestones, Sprints, Components
          |  unchanged          |  Work:     Board, Backlog, Reports
          |                     |  Team:     My Developer Profile, Developers, Technologies
          |                     |  Configuration
```

- **Software projects** have the *Software Project* box ticked. Projects created from Dev Projects get it automatically. Only these appear in Dev Projects and get keys, board columns and the Dev behaviour.
- **Regular projects** (marketing, office, etc.) behave exactly like plain Odoo.
- The Project app hides software projects by default with a **"Hide Software Projects"** filter. It's a normal search filter, so removing it shows everything.
- To move an existing project into Dev Projects, tick *Software Project* on it. It gets a key, board columns, and its existing tasks get numbered.

---

## Getting started

### Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Compose included)

### 1. Start Odoo

From the project folder:

```bash
docker compose up -d
```

This starts two containers:

| Container           | What it is              | Port   |
|---------------------|-------------------------|--------|
| `odoo_dev_web`      | Odoo 17                 | 8069   |
| `odoo_dev_database` | PostgreSQL 17           | (internal) |

Open **http://localhost:8069**.

### 2. Create a database

If you have no database yet, Odoo shows the database manager. Create one (for example `ProjectsData`), then log in.

### 3. Install the module

1. Go to **Apps**.
2. Remove the "Apps" filter and search for **Dev Projects**.
3. Click **Activate**.

The **Project** app is installed automatically if you don't have it.

### After changing the code

- **Python changes:** restart the web container with `docker restart odoo_dev_web`.
- **View/XML, field or translation changes:** upgrade the module, either from *Apps → Dev Projects → Upgrade* or from the command line:

  ```bash
  docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
      -d ProjectsData -u dev_addons --stop-after-init
  docker restart odoo_dev_web
  ```

> **Module name:** the module's folder is `dev_addons/` itself, so its technical name is **`dev_addons`** (shown as "Dev Projects" in Apps). Docker mounts it at `/mnt/extra-addons/dev_addons`. Older databases that installed it as `dev_projects` need the module renamed before upgrading.

---

## Day-to-day workflow

**In one line:** set up Components and Milestones → write issues in the **Backlog** → plan and **Start** a sprint → drag cards on the **Board** → **Complete Sprint** and read the recap → repeat → **Mark the milestone as Complete**.

How the pieces fit:

```
Project: AI glasses
├─ Milestones  → WHY / what goal?     "Login complete" (v1.2.0), "Beta launch"
├─ Sprints     → WHEN do we do it?    "Sprint 1", "Sprint 2"
└─ Components  → WHAT part is it?     "Login", "Camera", "UI"
```

One issue can have all three, e.g. **AG-4 Bug: Wrong password message**, with Milestone *Login complete*, Sprint *Sprint 1* and Component *Login*. Big issues can be split into sub-tasks.

### 1. Set up the project (once)
*Dev Projects → Planning → Projects → New*. Type the name and save; it gets a key (e.g. `AG`) and board columns. Then fill in the tabs:
- **Development:** check the key and paste the **GitHub Repository** link.
- **Components:** add the parts of your app with **Add a line**, e.g. *Login, Camera, UI*.
- **Milestones:** add your big goals with a deadline and, if you like, the version they ship as, e.g. *"Beta launch — Dec 1 — 1.0.0"*.

### 2. Write down the work (any time)
*Work → **Backlog***
- **Add a line** for each thing to do and pick its type: Story, Task, Bug or Improvement.
- Set its **Component**.
- Drag lines so the most important ones are at the top.
- For a big issue, open it (**View** at the end of the line) and add steps in its **Sub-tasks** tab.
- Check *Work → **Reports*** for what people outside the team sent: **Accept** puts it in the Backlog, **Decline** tells them why not.

### 3. Plan a sprint (every 1–2 weeks)
In the project's **Sprints** tab, or *Planning → Sprints*:
1. Create a sprint and pick the **Milestone** it works towards.
2. In the **Backlog**, set the **Sprint** column on the issues you'll do. They join the sprint's milestone automatically, and their sub-tasks come along.
3. Open the sprint and click **Start Sprint**.

### 4. Do the work (every day)
*Work → **Board***
- Drag cards: **To Do → In Progress → In Review → Done**. Each column shows the most important cards first.
- New issues created here go straight into the running sprint.

### 5. Finish the sprint
Open the sprint and click **Complete Sprint**. Unfinished issues go to the next sprint or back to the backlog. The **recap** opens: check the numbers, write a short summary and click **Save**. Then repeat from step 3.

### 6. Finish the milestone
When its goal is reached, open it (project **Milestones** tab) and click **Mark as Complete**.

**Buttons you can ignore at first**
- **Start / Send to Review / Mark as Done** on an issue do the same as dragging its card.
- **Pause / Resume** and **Assign to Me** are small shortcuts.
- **Complete** on an issue marks it done *and* takes the card off the Board (archive or delete). Use it only when you want the card gone.
- **Reopen** is only for something marked done by mistake.
- The **Project** menu is Odoo's normal app for non-software projects. You can work entirely in **Dev Projects**.

> **Why don't I see my sprint's issues on the Board?**
> The Board shows the *running* sprint plus issues not in any sprint. Issues in a sprint that hasn't been started stay hidden until you click **Start Sprint**. To see them earlier, use the sprint's **Issues** button or remove the "Current Work" filter.
>
> If you create an issue on the Board while no sprint is running, it goes to the backlog and a short notification tells you so.
>
> Sub-tasks never get their own card: open the parent issue to see them.

---

## Configuration

**Settings → Project → Dev Projects**

| Setting | Default | What it does |
|---------|---------|--------------|
| Technology Logo Folder | `/tech_images` | Folder searched for `<Technology name>.png` logos |
| Default Sprint Length (days) | 14 | Duration of new sprints |
| Default Board Columns for New Software Projects | On | Gives new software projects the four default columns |

**Dev Projects → Configuration → Board Columns**: rename, reorder or add columns, set each column's *Status Category* and *WIP Limit* (0 = no limit).

**Technology logos**: put PNG files in [`tech_images/`](tech_images/). The file name must match the technology name, ignoring upper/lower case. The folder is mounted read-only into the container at `/tech_images`.

---

## Languages (English / Spanish)

Every screen, button, message and the default columns are translated into Spanish ([`i18n/es.po`](dev_addons/i18n/es.po)). Odoo's own screens already come in Spanish. The language is chosen **per user**, so one person can work in English and another in Spanish.

1. **Once, as an administrator:** *Settings → General Settings → Languages → Add Languages*, pick a Spanish (e.g. *Spanish (DO) / Español (DO)* or *Spanish / Español*) and click **Add**. Any Spanish variant works: they all use the same translation file.
2. **Each user:** click your avatar (top right) → **Preferences** → **Language** → *Español*, then save. The page reloads in Spanish.

Main screens in each language:

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
| New Report / My Reports (📢 icon) | Nuevo reporte / Mis reportes |
| Reports (Dev Projects) | Reportes |

**Changing a text?** After editing a label or message in the code, export the template again and add the Spanish text to `es.po`, then upgrade the module:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d ProjectsData --i18n-export=/mnt/extra-addons/dev_addons/i18n/dev_addons.pot \
    --modules=dev_addons --stop-after-init
```

Texts missing from `es.po` simply show in English.

---

## Running the tests

Tests run on a **throwaway database**, so your real data is never touched:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d test_dev_addons -i dev_addons --test-enable --stop-after-init \
    --test-tags /dev_addons,/project,-/project:TestUi,-/project:TestProjectSharingChatterAccess
```

This runs the Dev Projects tests plus Odoo's own Project tests, to check that nothing in the Project app broke. Look for this line at the end:

```
0 failed, 0 error(s) of ... tests
```

`TestProjectSharingChatterAccess` is excluded because it also fails on a plain Odoo install, and `TestUi` needs a browser.

Afterwards, delete the test database:

```bash
docker exec odoo_dev_database dropdb -U odoo test_dev_addons
```

> On Windows Git Bash, put `MSYS_NO_PATHCONV=1` in front of the `docker compose run` command. PowerShell doesn't need it.

---

## Project structure

```
odoo_taskvc/
├── docker-compose.yaml        Odoo 17 + PostgreSQL 17
├── config_odoo/odoo.conf      Odoo server configuration
├── tech_images/               Technology logos (mounted at /tech_images)
├── logs/                      Odoo log file (git-ignored)
└── dev_addons/                The module itself, technical name "dev_addons" (mounted at /mnt/extra-addons/dev_addons)
    ├── __manifest__.py
    ├── hooks.py               Install / uninstall steps
    ├── data/                  Default board columns, settings
    ├── i18n/                  Translations: dev_addons.pot (template), es.po (Spanish)
    ├── migrations/            Upgrade steps (old Histories → Milestones; recaps for old sprints)
    ├── models/
    │   ├── project_task.py        Issues: types, keys, board/Done sync, sub-tasks, Complete wizard
    │   ├── project_project.py     Software projects, keys, screen actions
    │   ├── project_task_type.py   Board columns: status category, WIP limit
    │   ├── dev_sprint.py          Sprints, the Complete Sprint wizard and the sprint recap
    │   ├── project_milestone.py   Milestones: version, progress, sprints, Complete
    │   ├── dev_module.py          Components (parts of the software that classify issues)
    │   ├── dev_report.py          Reports: send, accept (→ issue, project picked then) or decline
    │   ├── dev_technology.py      Technologies and logo loading
    │   ├── res_partner.py         Developer profiles and access codes
    │   └── res_config_settings.py Settings
    ├── views/                 Board, backlog, reports, milestones, sprints, components, forms, menus, settings
    ├── security/              Access rights (everyone can send reports and sees only their own)
    ├── static/
    │   ├── description/       App icon
    │   └── src/report_systray/ The 📢 report icon in the top bar
    └── tests/
        ├── test_dev_projects.py   Behaviour tests
        ├── test_reports.py        Reports: sending, accepting, declining, who sees what
        └── test_screens.py        Every screen opens; Project app still works
```

`data_generator.py` and `csv/` belong to the earlier `manage` module, which has been removed. Dev Projects doesn't use them.

---

## Uninstalling

Uninstalling Dev Projects from *Apps* puts the Project app back the way Odoo ships it: original menus, no default filter. Your projects and tasks stay, sub-tasks included (they're Odoo's own). Only the Dev fields, sprints and their recaps, components and technologies are removed. Milestones stay, because they belong to Odoo's Project app.

---

## License

LGPL-3
