# -*- coding: utf-8 -*-
{
    'name': "Dev Projects",
    'summary': "Jira-style software development on top of Odoo Project: issue types, keys, backlog, milestones, sprints, WIP limits",
    'description': """
Adds a "Dev Projects" app that works on the same projects and tasks as Odoo's
Project app, so you can switch between the two:

* Issues are project tasks with a type (Story, Task, Bug, Improvement),
  story points, bug severity, and a key per project (WEB-1, WEB-2...).
* Backlog ranked by drag and drop; sprints you start and complete by hand,
  moving unfinished work to the next sprint or back to the backlog.
* Board columns are project stages with a status category and a WIP limit.
* One assignee (kept in the task's assignees) and a reporter per issue.
* Milestones (goals with a deadline) that group sprints and issues.
* A GitHub repository link per project.
* Technologies, and developer profiles with access codes.
* Complete an issue to archive or delete it.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Services/Project',
    'version': '17.0.1.1.0',
    'license': 'LGPL-3',
    'application': True,
    'depends': ['project', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/dev_data.xml',
        'views/stage_views.xml',
        'views/task_views.xml',
        'views/sprint_views.xml',
        'views/milestone_views.xml',
        'views/project_views.xml',
        'views/technology_views.xml',
        'views/developer_views.xml',
        'views/project_app_views.xml',
        'views/settings_views.xml',
        'views/menus.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
}
