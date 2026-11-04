# -*- coding: utf-8 -*-
{
    'name': "Software Projects Plus",
    'summary': "Jira-style issue tracking for Software Projects: one issue model, keys, backlog, sprints, board columns",
    'description': """
Extends the Software Projects (manage) module into a Jira-style tracker:

* One issue model with a type (Story, Task, Bug, Improvement); old bugs and
  improvements are moved into it on install/upgrade, comments included.
* Project keys: issues are numbered per project (WEB-1, WEB-2...).
* Backlog ranked by drag and drop, sprints started and completed by hand,
  with unfinished work moved to the next sprint or back to the backlog.
* One assignee and a reporter per issue.
* Board columns you can add, rename and reorder, with WIP limits.
* Chatter, activities, deadlines, story points, bug severity, date checks.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Services/Project',
    'version': '17.0.2.0.0',
    'license': 'LGPL-3',
    'depends': ['manage', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/manage_plus_data.xml',
        'views/task_views.xml',
        'views/sprint_views.xml',
        'views/project_views.xml',
        'views/history_views.xml',
        'views/technology_views.xml',
        'views/developer_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
