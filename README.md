
[README -.md](https://github.com/user-attachments/files/34446706/README.-.Copy.md)
# Dev Projects for Odoo 17

Jira-style software project management built on top of Odoo's own **Project** app.

Dev Projects adds issue keys (`WEB-1`, `WEB-2`…), issue types, a board with WIP limits, a ranked backlog, sprints you start and complete by hand, milestones, modules, technologies and developer profiles. It works on the **same projects and tasks** as the Project app. An issue is a normal Odoo task with extra fields, so you can switch between the two apps at any time.

---

## Contents

- [Features](#features)
- [How it fits with the Project app](#how-it-fits-with-the-project-app)
- [Getting started](#getting-started)
- [Day-to-day workflow](#day-to-day-workflow)
- [Configuration](#configuration)
- [Running the tests](#running-the-tests)
- [Project structure](#project-structure)
- [Uninstalling](#uninstalling)

---

## Features

**Issues**
- Types: Story, Task, Bug, Improvement.
- A key per project, e.g. `AG-1`, `AG-2`. It's suggested from the project name ("AI glasses" → `AG`), and you can search by it.
- Story points, a 4-level priority (Normal, Important, High, Critical) and a severity for bugs.
- One **assignee** (also added to the task's assignees in Odoo) and a **reporter**.
- Start/finish dates filled in automatically as the issue moves across the board.
- Pause/resume, overdue warnings, and **Complete**: mark it done, then archive or delete it.

**Board**
- Columns are Odoo project stages, each with a status category: To Do, In Progress, In Review or Done.
- Moving a card to a Done column marks the task done in the Project app too, and moving it out reopens it.
- Optional **WIP limit** per column, counted per project and sprint. Done columns are never limited.
- Shows **current work**: the running sprint plus issues not in any sprint.

**Backlog and sprints**
- Backlog grouped by sprint. Drag to rank issues, and pick a sprint to plan them.
- Sprints are started and completed by hand, like in Jira. Only one sprint per project can run at a time.
- When you complete a sprint, unfinished issues move to the next sprint or back to the backlog.
- Sprint progress, planned points and done points.

**Milestones**
- A milestone is a goal with a deadline, e.g. *"Login complete — Nov 20"*. It groups **sprints** and **issues**:
  ```
  Project: AI glasses
  └─ Milestone: Login complete (due Nov 20)   ███░░ 60%
     ├─ Sprint 1 → AG-1 Story: login form, AG-2 Bug: wrong password message
     └─ Sprint 2 → AG-3 Improvement: Google login
  ```
- Link a sprint to a milestone, and every issue in that sprint joins the milestone automatically. An issue can also be given a milestone directly.
- Each milestone shows its progress (issues and story points done), bugs and technologies used. It turns red with a **Late** ribbon after its deadline, and has a **Mark as Complete** button.
- These are Odoo's own milestones, so the Project app shows the same ones.

**Projects**
- A **GitHub Repository** link on each software project.
- The project form has the tabs **Development | Milestones | Sprints | Modules | Description | Settings**. Milestones, Sprints and Modules only appear on software projects.
- Software projects call their tasks **Issues**, and hide Odoo's "Name of the Tasks" and Tags fields. Odoo's **Tasks** button is replaced by **Open Issues**.

**Modules**
- Modules are the parts of your software, e.g. *Login*, *Payments*, *Camera*. Each project has its own list.
- Pick one in the **Module** field of an issue (under Dev Priority). Typing a new name offers to create it on the spot.
- Each module has an optional **Lead** and shows its issues, open issues, open bugs and technologies used. The Board cards, issue lists and Backlog show the module, and you can filter or group by it.
- Duplicating a project copies its modules too.

**Technologies and developers**
- Technologies get their logo automatically from an image folder (`Docker` → `Docker.png`).
- Developer profiles on contacts:
  - An access code: 8 digits followed by letters, e.g. `12345678A`. It must be unique and can't be changed once saved.
  - Technologies the developer knows.
  - A "Devs" tag, added automatically.
  - A **Create User** button that gives the developer an Odoo login (their email), so issues can be assigned to them. It links the login to the same contact, so the profile stays.

---

## How it fits with the Project app

After installing, the home screen shows one **Projects** app with two menus:

```
Projects  |  Project ▾          |  Dev Projects ▾
          |  Odoo's own menus,  |  Planning: Projects, Milestones, Sprints, Modules
          |  unchanged          |  Work:     Board, Backlog
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
- **View/XML or field changes:** upgrade the module, either from *Apps → Dev Projects → Upgrade* or from the command line:

  ```bash
  docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
      -d ProjectsData -u dev_projects --stop-after-init
  docker restart odoo_dev_web
  ```

---

## Day-to-day workflow

**In one line:** set up Modules and Milestones → write issues in the **Backlog** → plan and **Start** a sprint → drag cards on the **Board** → **Complete Sprint** → repeat → **Mark the milestone as Complete**.

How the pieces fit:

```
Project: AI glasses
├─ Milestones  → WHY / what goal?     "Login complete", "Beta launch"
├─ Sprints     → WHEN do we do it?    "Sprint 1", "Sprint 2"
└─ Modules     → WHAT part is it?     "Login", "Camera", "UI"
```

One issue can have all three, e.g. **AG-4 Bug: Wrong password message**, with Milestone *Login complete*, Sprint *Sprint 1* and Module *Login*.

### 1. Set up the project (once)
*Dev Projects → Planning → Projects → New*. Type the name and save; it gets a key (e.g. `AG`) and board columns. Then fill in the tabs:
- **Development:** check the key and paste the **GitHub Repository** link.
- **Modules:** add the parts of your app with **Add a line**, e.g. *Login, Camera, UI*.
- **Milestones:** add your big goals with a deadline, e.g. *"Beta launch — Dec 1"*.

### 2. Write down the work (any time)
*Work → **Backlog***
- **Add a line** for each thing to do and pick its type: Story, Task, Bug or Improvement.
- Set its **Module**.
- Drag lines so the most important ones are at the top.

### 3. Plan a sprint (every 1–2 weeks)
In the project's **Sprints** tab, or *Planning → Sprints*:
1. Create a sprint and pick the **Milestone** it works towards.
2. In the **Backlog**, set the **Sprint** column on the issues you'll do. They join the sprint's milestone automatically.
3. Open the sprint and click **Start Sprint**.

### 4. Do the work (every day)
*Work → **Board***
- Drag cards: **To Do → In Progress → In Review → Done**.
- New issues created here go straight into the running sprint.

### 5. Finish the sprint
Open the sprint and click **Complete Sprint**. Unfinished issues go to the next sprint or back to the backlog. Then repeat from step 3.

### 6. Finish the milestone
When its goal is reached, open it (project **Milestones** tab) and click **Mark as Complete**.

**Buttons you can ignore at first**
- **Start / Send to Review / Mark as Done** on an issue do the same as dragging its card.
- **Pause / Resume** and **Assign to Me** are small shortcuts.
- **Complete** on an issue marks it done *and* takes the card off the board (archive or delete). Use it only when you want the card gone.
- **Reopen** is only for something marked done by mistake.
- The **Project** menu is Odoo's normal app for non-software projects. You can work entirely in **Dev Projects**.

> **Why don't I see my sprint's issues on the Board?**
> The Board shows the *running* sprint plus issues not in any sprint. Issues in a sprint that hasn't been started stay hidden until you click **Start Sprint**. To see them earlier, use the sprint's **Issues** button or remove the "Current Work" filter.
>
> If you create an issue on the Board while no sprint is running, it goes to the backlog and a short notification tells you so.

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

## Running the tests

Tests run on a **throwaway database**, so your real data is never touched:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo \
    -d test_dev_projects -i dev_projects --test-enable --stop-after-init \
    --test-tags /dev_projects,/project,-/project:TestUi,-/project:TestProjectSharingChatterAccess
```

This runs the Dev Projects tests plus Odoo's own Project tests, to check that nothing in the Project app broke. Look for this line at the end:

```
0 failed, 0 error(s) of ... tests
```

`TestProjectSharingChatterAccess` is excluded because it also fails on a plain Odoo install, and `TestUi` needs a browser.

Afterwards, delete the test database:

```bash
docker exec odoo_dev_database dropdb -U odoo test_dev_projects
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
└── dev_addons/                Custom addons (mounted at /mnt/extra-addons)
    └── dev_projects/
        ├── __manifest__.py
        ├── hooks.py           Install / uninstall steps
        ├── data/              Default board columns, settings
        ├── migrations/        Upgrade steps (e.g. turning old Histories into Milestones)
        ├── models/
        │   ├── project_task.py        Issues: types, keys, board/Done sync, Complete wizard
        │   ├── project_project.py     Software projects, keys, screen actions
        │   ├── project_task_type.py   Board columns: status category, WIP limit
        │   ├── dev_sprint.py          Sprints and the Complete Sprint wizard
        │   ├── project_milestone.py   Milestones: progress, sprints, Complete
        │   ├── dev_module.py          Modules: parts of the software that classify issues
        │   ├── dev_technology.py      Technologies and logo loading
        │   ├── res_partner.py         Developer profiles and access codes
        │   └── res_config_settings.py Settings
        ├── views/             Board, backlog, milestones, sprints, modules, forms, menus, settings
        ├── security/          Access rights
        └── tests/
            ├── test_dev_projects.py   Behaviour tests
            └── test_screens.py        Every screen opens; Project app still works
```

`data_generator.py` and `csv/` belong to the earlier `manage` module, which has been removed. Dev Projects doesn't use them.

---

## Uninstalling

Uninstalling Dev Projects from *Apps* puts the Project app back the way Odoo ships it: original menus, no default filter. Your projects and tasks stay. Only the Dev fields, sprints, modules and technologies are removed. Milestones stay, because they belong to Odoo's Project app.

---

## License

LGPL-3
