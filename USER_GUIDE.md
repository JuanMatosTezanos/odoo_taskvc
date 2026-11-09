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
6. [Splitting work into sub-tasks](#6-splitting-work-into-sub-tasks)
7. [Planning a sprint](#7-planning-a-sprint)
8. [Doing the work: the Board](#8-doing-the-work-the-board)
9. [Finishing a sprint and reading its recap](#9-finishing-a-sprint-and-reading-its-recap)
10. [Finishing a milestone](#10-finishing-a-milestone)
11. [Finding things](#11-finding-things)
12. [Using Dev Projects in Spanish](#12-using-dev-projects-in-spanish)
13. [Reporting a problem or an idea (for everyone)](#13-reporting-a-problem-or-an-idea-for-everyone)
14. [Reviewing reports](#14-reviewing-reports)
15. [Adding a new team member](#15-adding-a-new-team-member)
16. [Common questions](#16-common-questions)

---

## 1. Opening Dev Projects

1. Open the web address your company gave you and log in with your email and password.
2. Click the **Projects** app on the home screen.
3. At the top you'll see two menus: **Project** and **Dev Projects**. Use **Dev Projects** for software work.

> **Not on the dev team?** You won't see the Projects app, and you don't need it. Click the 📢 icon at the top right of any screen to send a problem or an idea (see section 13).

The **Dev Projects** menu has four parts:

| Menu | What's inside |
|---|---|
| **Planning** | Projects, Milestones, Sprints, Components: the big picture |
| **Work** | Board, Backlog and Reports: the day-to-day work |
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
| **Sub-task** | A smaller step inside an issue | *"Design the button"*, *"Write the code"* |
| **Backlog** | The waiting list of all work not started yet | |
| **Sprint** | A short work period, usually 1–2 weeks | *Sprint 1* |
| **Recap** | The summary of a finished sprint | *"12 of 15 issues finished"* |
| **Board** | The screen with columns where you move work forward | |
| **Report** | A problem or idea sent by someone outside the dev team | *"Can't print invoices"* |
| **Milestone** | A big goal with a deadline | *"Beta launch by Dec 1"* |
| **Version** | The version number a milestone comes out as | *1.0.0* |
| **Component** | A part of the app | *Login, Camera, Settings* |
| **Story points** | A rough size of the work (bigger number = more effort) | *1, 3, 5, 8* |
| **Assignee** | The person doing the work | |
| **Reported by** | The person who created the issue | |

---

## 3. How it all fits together

```
Project: AI glasses
├─ Milestones → What goal are we working towards?   "Beta launch" (version 1.0.0)
├─ Sprints    → When are we doing it?               "Sprint 1"
└─ Components → Which part of the app is it?        "Camera"
```

Every piece of work (an **issue**) can be labelled with all three. For example:

> **AG-4 Bug: Wrong password message**
> Milestone: *Beta launch* · Sprint: *Sprint 1* · Component: *Login*

Big issues can be split into smaller **sub-tasks** (see section 6).

**The usual cycle:**

**Backlog** (write it down) → **Sprint** (choose what to do next) → **Board** (do it) → **Finish the sprint** (read the recap) → repeat

---

## 4. Setting up a project (once)

Usually a manager does this.

1. Go to **Dev Projects → Planning → Projects** and click **New**.
2. Type the project name and save. The project automatically gets a short **key** (e.g. "AI glasses" gets **AG**) and its columns on the **Board**.
3. Fill in the tabs at the bottom of the project:
   - **Development:** paste the link to the project's code (GitHub), if you have one.
   - **Components:** click **Add a line** and add the parts of your app, e.g. *Login*, *Camera*, *Settings*.
   - **Milestones:** click **Add a line** and add your big goals with a deadline, e.g. *"Beta launch"*, due *Dec 1*.

**Giving a milestone a version:** open the milestone and type its **Version**, e.g. *1.0.0*. Only version numbers are accepted, like *1.0*, *1.2.0* or *v2.0.1*. Words like "beta" alone aren't, but *2.1.0-beta* is fine.

---

## 5. Adding work

Go to **Dev Projects → Work → Backlog**.

1. Click **Add a line**.
2. Type a short title, e.g. *"Photo button doesn't respond"*.
3. Pick the **type**: Story, Task, Bug or Improvement.
4. Pick the **Component**: which part of the app it's about.
5. Optionally pick who will do it (**Assignee**) and how big it is (**Story Points**).

**Order matters:** drag lines up and down so the most important work is at the top.

**Opening an issue:** clicking a line only lets you edit it right there. To see the whole issue (description, screenshots, deadline, sub-tasks), click **View** at the right end of the line. **Reported by** shows who created it; it's filled in for you.

---

## 6. Splitting work into sub-tasks

When an issue is big, split it into smaller steps.

1. Open the issue.
2. Go to its **Sub-tasks** tab.
3. Click **Add a line** for each step, e.g. *"Design the button"*, *"Write the code"*, *"Test it"*.

Good to know:

- Each sub-task gets its own key (e.g. **AG-7**), and you can open it like any issue.
- Sub-tasks always belong to the same sprint as their issue. When the issue moves to another sprint, its sub-tasks move with it.
- Sub-tasks don't get their own card on the **Board**. The issue's card shows how many are done instead, e.g. **☑ 2/5**.
- Sub-tasks have no story points: the issue they belong to counts.

---

## 7. Planning a sprint

A sprint is a short period, usually 1–2 weeks, where the team commits to a set of work.

1. Go to **Dev Projects → Planning → Sprints** (or the **Sprints** tab of your project) and click **New**.
2. Choose the **Milestone** this sprint works towards.
3. Go back to the **Backlog** and, for each issue you want to do in this sprint, set the **Sprint** column.
4. When the team is ready, open the sprint and click **Start Sprint**.

Only one sprint per project can be running at a time.

---

## 8. Doing the work: the Board

Go to **Dev Projects → Work → Board**. This is where you'll spend most of your time.

The **Board** has four columns:

**To Do → In Progress → In Review → Done**

- Each column shows the **most important cards first**: serious bugs (Critical or Blocker) at the very top, then by priority stars. To move a card up, give it more stars.
- **Drag a card** to the next column as the work moves along.
- Moving a card to **In Progress** records when you started; moving it to **Done** records when you finished.
- Click a card to open it, write comments, or attach files.
- To take an issue yourself, open it and click **Assign to Me**.
- New issues created on the **Board** go straight into the running sprint.

**What the Board shows:** the work in the **running sprint**, plus work not planned in any sprint yet.

---

## 9. Finishing a sprint and reading its recap

At the end of the sprint:

1. Open the sprint (**Planning → Sprints**).
2. Click **Complete Sprint**.
3. Choose where unfinished work should go: the **next sprint** or back to the **Backlog**.
4. The sprint's **recap** opens. It shows:
   - how many issues and story points were finished, out of everything in the sprint;
   - what was finished by type (e.g. how many bugs were fixed), by component and by person;
   - the list of finished issues, and the unfinished ones with where they went.
5. Write a few lines in the **Sprint Summary** box about what the sprint was about, then click **Save**.

You can read the recap again any time: open the finished sprint and it shows its **Recap** tab first. You can also edit the summary there.

Then plan the next sprint (see section 7).

---

## 10. Finishing a milestone

When the goal is reached:

1. Open the project, go to the **Milestones** tab, and click the milestone.
2. Click **Mark as Complete**.

Each milestone shows a **progress bar** so you can see how close you are. If the deadline passes before it's complete, it turns **red** and shows **Late**.

---

## 11. Finding things

At the top of the **Board** and the **Backlog** there's a **search bar**. Click the small arrow next to it for ready-made filters:

| Filter | Shows |
|---|---|
| **Assigned to Me** | Your own work |
| **Reported by Me** | Work you created |
| **Bugs** | Only bugs |
| **Open** | Everything not finished |
| **Overdue** | Work past its deadline |
| **High Priority** | Important work |
| **No Component** / **No Milestone** | Work that still needs labelling |
| **Archived** | Work that was completed and removed from the Board |

You can also type an issue's key, e.g. **AG-12**, to find it straight away.

---

## 12. Using Dev Projects in Spanish

Everyone can choose their own language: you can work in English while a teammate works in Spanish.

**To switch to Spanish:**

1. Click your picture or initials at the top right.
2. Click **Preferences**.
3. Change **Language** to **Español** and save.

The page reloads in Spanish. To go back, choose **English** the same way.

If you don't see **Español** in the list, ask a manager to add it once in **Settings → General Settings → Languages → Add Languages**.

Some names change in Spanish: **Issues** become **Incidencias**, **Milestones** become **Hitos**, **Components** become **Componentes**, **Sub-tasks** become **Subtareas**, the **Recap** is the **Resumen**, the **Board** is the **Tablero**, and **New Report** / **My Reports** are **Nuevo reporte** / **Mis reportes**. **Backlog** and **Sprints** keep their names.

---

## 13. Reporting a problem or an idea (for everyone)

You don't need to be a developer for this. Anyone in the company can tell the dev team about something.

1. Click the 📢 icon at the top right of the screen (next to the chat and clock icons). It's there on every screen.
2. Click **New Report**. A small window opens.
3. Fill in:
   - **Title**: a few words, e.g. *"Can't print invoices"*.
   - **App**: the app where it happens, e.g. *Sales* or *Inventory*. You must pick one.
   - **What is it?**: *Something's broken*, *Request a feature* or *Question*.
   - **How urgent is it?**: from *It can wait* to *I can't work*.
   - **Details**: what happened, what you expected, and how to see it again. You can paste screenshots here.
4. Click **Send**. You'll see a short "Thanks!" message.

**Reported by** is filled in with your name, so the team knows who sent it.

**Following it:** click the 📢 icon → **My Reports**. Each report shows where it stands:

**Waiting for review → Accepted → Being worked on → Done**

If the team decides not to do it, it shows **Declined** with the reason. You'll get a notification when it's accepted or declined, and again when the work is done. You can also write to the team at the bottom of the report.

You only see your own reports. Once the team has reviewed a report it can't be edited, but you can still add a message.

---

## 14. Reviewing reports

*For the dev team.*

Go to **Dev Projects → Work → Reports**. It opens on the reports **To Review**. Each one shows the **App** it's about and who sent it.

Open a report and choose:

- **Accept**: pick the **project** whose Backlog it goes to. The project is suggested when there's only one, or when a report from the same app went to a project before. It becomes an issue in that **Backlog**, with:
  - the person who sent it as **Reported by**;
  - their details, screenshots and the app copied over;
  - the type from the report (*Something's broken* = Bug, *Request a feature* = Story, *Question* = Task), and the priority too.

  From there, plan it like any other issue. When it's done, the person who sent it is told automatically.
- **Decline**: write a short, friendly reason. The person who sent it will see it.

To accept several at once, tick them in the list and use **Actions → Accept**. Declined by mistake? Open it and click **Review Again**.

---


## 15. Adding a new team member

*For managers.*

To give work to someone, they need a login:

1. Go to **Dev Projects → Team → Developers** and open (or create) the person.
2. Make sure their **email** is filled in, and save.
3. Click **Create User** on the blue message.
4. They can then log in with their email. Send them an invitation from **Settings → Users** so they can choose a password, or set one for them.

Each developer also has an **access code**: 8 numbers followed by letters, e.g. **12345678A**. Once saved, it can't be changed.

---

## 16. Common questions

**I created an issue but can't see it on the Board.**
It's probably in a sprint that hasn't started yet. The **Board** only shows the *running* sprint. Ask your manager to click **Start Sprint**, or find the issue in the **Backlog**.

**I added a sub-task but it's not on the Board.**
That's normal: sub-tasks live inside their issue. Open the issue and look at its **Sub-tasks** tab.

**A message said my issue "went to the backlog".**
No sprint was running, so the issue was saved in the Backlog. Nothing is lost.

**My card disappeared after I clicked "Complete".**
**Complete** marks the work as done and removes it from the **Board**. To see it again, use the **Archived** filter.

**I can't move a card into a column.**
That column has a limit on how many cards it can hold at once. Finish something in that column first, or ask a manager to raise the limit.

**The milestone won't accept my version.**
The **Version** box only takes version numbers, like *1.0*, *1.2.0* or *v2.0.1*.

**I can't pick someone as the Assignee.**
They don't have a login yet. A manager can create one (see section 15).

**What's the "Project" menu next to "Dev Projects"?**
It's for the company's other, non-software projects. For software work, use **Dev Projects**.

**I clicked something by mistake.**
- Marked as done by mistake → open the issue and click **Reopen**.
- Moved a card to the wrong column → just drag it back.

---

*Need more help? Ask your project manager.*
