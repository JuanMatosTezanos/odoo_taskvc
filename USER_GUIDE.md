# Dev Projects: User Guide

*Versión en español: [GUIA_DE_USUARIO.md](GUIA_DE_USUARIO.md)*

Dev Projects helps your team plan and track work on software: what needs doing, who is doing it, and how close you are to your goals. Think of it as a shared to-do board for the whole team.

You don't need any technical knowledge to use it. This guide walks you through everything step by step.

---

## Contents

1. [Opening Dev Projects](#1-opening-dev-projects)
2. [Words you'll see](#2-words-youll-see)
3. [How it all fits together](#3-how-it-all-fits-together)
4. [Setting up a project (once)](#4-setting-up-a-project-once)
5. [Adding work](#5-adding-work)
6. [Planning a sprint](#6-planning-a-sprint)
7. [Doing the work: the Board](#7-doing-the-work-the-board)
8. [Finishing a sprint](#8-finishing-a-sprint)
9. [Finishing a milestone](#9-finishing-a-milestone)
10. [Finding things](#10-finding-things)
11. [Adding a new team member](#11-adding-a-new-team-member)
12. [Common questions](#12-common-questions)

---

## 1. Opening Dev Projects

1. Open the web address your company gave you and log in with your email and password.
2. Click the **Projects** app on the home screen.
3. At the top you'll see two menus: **Project** and **Dev Projects**. Use **Dev Projects** for software work.

The **Dev Projects** menu has four parts:

| Menu | What's inside |
|---|---|
| **Planning** | Projects, Milestones, Sprints, Modules: the big picture |
| **Work** | Board and Backlog: the day-to-day work |
| **Team** | Your developer profile, the developers, and the technologies you use |
| **Configuration** | Settings (managers only) |

---

## 2. Words you'll see

| Word | What it means | Example |
|---|---|---|
| **Project** | The product you're building | *AI glasses* |
| **Issue** | One piece of work | *"Add a login button"* |
| **Key** | The issue's short code, like a ticket number | *AG-12* |
| **Story** | Something new a user will be able to do | *"Users can reset their password"* |
| **Task** | A general job to get done | *"Update the logo"* |
| **Bug** | Something that's broken | *"App crashes when taking a photo"* |
| **Improvement** | Making something that works even better | *"Make the camera faster"* |
| **Backlog** | The waiting list of all work not started yet | |
| **Sprint** | A short work period, usually 1–2 weeks | *Sprint 1* |
| **Board** | The screen with columns where you move work forward | |
| **Milestone** | A big goal with a deadline | *"Beta launch by Dec 1"* |
| **Module** | A part of the app | *Login, Camera, Settings* |
| **Story points** | A rough size of the work (bigger number = more effort) | *1, 3, 5, 8* |
| **Assignee** | The person doing the work | |
| **Reporter** | The person who created the issue | |

---

## 3. How it all fits together

```
Project: AI glasses
├─ Milestones → What goal are we working towards?   "Beta launch"
├─ Sprints    → When are we doing it?               "Sprint 1"
└─ Modules    → Which part of the app is it?        "Camera"
```

Every piece of work (an **issue**) can be labelled with all three. For example:

> **AG-4 Bug: Wrong password message**
> Milestone: *Beta launch* · Sprint: *Sprint 1* · Module: *Login*

**The usual cycle:**

**Backlog** (write it down) → **Sprint** (choose what to do next) → **Board** (do it) → **Finish the sprint** → repeat

---

## 4. Setting up a project (once)

Usually a manager does this.

1. Go to **Dev Projects → Planning → Projects** and click **New**.
2. Type the project name and save. The project automatically gets a short **key** (e.g. "AI glasses" gets **AG**) and a board.
3. Fill in the tabs at the bottom of the project:
   - **Development:** paste the link to the project's code (GitHub), if you have one.
   - **Modules:** click **Add a line** and add the parts of your app, e.g. *Login*, *Camera*, *Settings*.
   - **Milestones:** click **Add a line** and add your big goals with a deadline, e.g. *"Beta launch"*, due *Dec 1*.

---

## 5. Adding work

Go to **Dev Projects → Work → Backlog**.

1. Click **Add a line**.
2. Type a short title, e.g. *"Photo button doesn't respond"*.
3. Pick the **type**: Story, Task, Bug or Improvement.
4. Pick the **Module**: which part of the app it's about.
5. Optionally pick who will do it (**Assignee**) and how big it is (**Story Points**).

**Order matters:** drag lines up and down so the most important work is at the top.

To add more detail (a description, screenshots, a deadline), click the issue to open it.

---

## 6. Planning a sprint

A sprint is a short period, usually 1–2 weeks, where the team commits to a set of work.

1. Go to **Dev Projects → Planning → Sprints** (or the **Sprints** tab of your project) and click **New**.
2. Choose the **Milestone** this sprint works towards.
3. Go back to the **Backlog** and, for each issue you want to do in this sprint, set the **Sprint** column.
4. When the team is ready, open the sprint and click **Start Sprint**.

Only one sprint per project can be running at a time.

---

## 7. Doing the work: the Board

Go to **Dev Projects → Work → Board**. This is where you'll spend most of your time.

The Board has four columns:

**To Do → In Progress → In Review → Done**

- **Drag a card** to the next column as the work moves along.
- Moving a card to **In Progress** records when you started; moving it to **Done** records when you finished.
- Click a card to open it, write comments, or attach files.
- To take an issue yourself, open it and click **Assign to Me**.
- New issues created on the Board go straight into the running sprint.

**What the Board shows:** the work in the **running sprint**, plus work not planned in any sprint yet.

---

## 8. Finishing a sprint

At the end of the sprint:

1. Open the sprint (**Planning → Sprints**).
2. Click **Complete Sprint**.
3. Choose where unfinished work should go: the **next sprint** or back to the **Backlog**.

Then plan the next sprint (see section 6).

---

## 9. Finishing a milestone

When the goal is reached:

1. Open the project, go to the **Milestones** tab, and click the milestone.
2. Click **Mark as Complete**.

Each milestone shows a **progress bar** so you can see how close you are. If the deadline passes before it's complete, it turns **red** and shows **Late**.

---

## 10. Finding things

At the top of the Board and Backlog there's a **search bar**. Click the small arrow next to it for ready-made filters:

| Filter | Shows |
|---|---|
| **Assigned to Me** | Your own work |
| **Bugs** | Only bugs |
| **Open** | Everything not finished |
| **Overdue** | Work past its deadline |
| **High Priority** | Important work |
| **No Module** / **No Milestone** | Work that still needs labelling |
| **Archived** | Work that was completed and removed from the Board |

You can also type an issue's key, e.g. **AG-12**, to find it straight away.

---

## 11. Adding a new team member

*For managers.*

To give work to someone, they need a login:

1. Go to **Dev Projects → Team → Developers** and open (or create) the person.
2. Make sure their **email** is filled in, and save.
3. Click **Create User** on the blue message.
4. They can then log in with their email. Send them an invitation from **Settings → Users** so they can choose a password, or set one for them.

Each developer also has an **access code**: 8 numbers followed by letters, e.g. **12345678A**. Once saved, it can't be changed.

---

## 12. Common questions

**I created an issue but can't see it on the Board.**
It's probably in a sprint that hasn't started yet. The Board only shows the *running* sprint. Ask your manager to click **Start Sprint**, or find the issue in the **Backlog**.

**A message said my issue "went to the backlog".**
No sprint was running, so the issue was saved in the Backlog. Nothing is lost.

**My card disappeared after I clicked "Complete".**
**Complete** marks the work as done and removes it from the Board. To see it again, use the **Archived** filter.

**I can't move a card into a column.**
That column has a limit on how many cards it can hold at once. Finish something in that column first, or ask a manager to raise the limit.

**I can't pick someone as the Assignee.**
They don't have a login yet. A manager can create one (see section 11).

**What's the "Project" menu next to "Dev Projects"?**
It's for the company's other, non-software projects. For software work, use **Dev Projects**.

**I clicked something by mistake.**
- Marked as done by mistake → open the issue and click **Reopen**.
- Moved a card to the wrong column → just drag it back.

---

*Need more help? Ask your project manager.*
