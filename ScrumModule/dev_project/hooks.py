# -*- coding: utf-8 -*-
"""Install / uninstall steps for Dev Projects."""

# Project app actions that hide software projects by default, with the
# context Odoo ships them with (restored on uninstall).
PROJECT_ACTION_CONTEXTS = {
    'project.open_view_project_all': "{}",
    'project.open_view_project_all_group_stage': "{}",
    'project.open_view_project_all_config': "{}",
    'project.open_view_project_all_config_group_stage': "{}",
    'project.action_view_all_task': "{'search_default_open_tasks': 1, 'default_user_ids': [(4, uid)]}",
    'project.action_view_my_task': "{'search_default_open_tasks': 1, 'all_task': 0, 'default_user_ids': [(4, uid)]}",
    'project.action_project_task_user_tree': "{'group_by_no_leaf':1, 'group_by':[], 'graph_measure': '__count__'}",
}

PROJECT_MENUS = ('project.menu_projects', 'project.menu_projects_group_stage',
                 'project.menu_project_management', 'project.menu_project_report',
                 'project.menu_project_config')


def enable_milestones(env):
    """Dev Projects plans with Odoo's milestones: switch the feature on (the same
    as ticking Settings > Project > Milestones) and on every software project."""
    group = env.ref('project.group_project_milestone')
    for xmlid in ('base.group_user', 'base.group_portal'):
        env.ref(xmlid).write({'implied_ids': [(4, group.id)]})
    software = env['project.project'].with_context(active_test=False).search([('dev_is_software', '=', True)])
    software.write(software._dev_software_defaults())


def post_init_hook(env):
    enable_milestones(env)
    # Existing projects stay regular projects (tick "Software Project" to move
    # one to Dev Projects). Existing columns get a status category guessed
    # from their name, for when they are used by a software project.
    Stage = env['project.task.type']
    ours = Stage._dev_default_stages()
    for stage in Stage.with_context(active_test=False).search([('id', 'not in', ours.ids)]):
        stage.dev_category = Stage._dev_guess_category(stage.name)


def uninstall_hook(env):
    """Put the Project app back the way Odoo ships it."""
    root = env.ref('project.menu_main_pm', raise_if_not_found=False)
    if root:
        root.name = 'Project'
        for xmlid in PROJECT_MENUS:
            menu = env.ref(xmlid, raise_if_not_found=False)
            if menu:
                menu.parent_id = root
    for xmlid, context in PROJECT_ACTION_CONTEXTS.items():
        action = env.ref(xmlid, raise_if_not_found=False)
        if action:
            action.context = context
