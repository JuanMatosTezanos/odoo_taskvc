# -*- coding: utf-8 -*-
"""Prepare data that existed in the Project app before Dev Projects was installed."""


def post_init_hook(env):
    Stage = env['project.task.type']
    ours = Stage._dev_default_stages()

    # Existing columns get a status category guessed from their name.
    for stage in Stage.with_context(active_test=False).search([('id', 'not in', ours.ids)]):
        stage.dev_category = Stage._dev_guess_category(stage.name)

    # Existing projects get a key; their issues get numbered in creation order.
    Project = env['project.project'].with_context(active_test=False)
    for project in Project.search([('dev_key', '=', False)], order='id'):
        project.dev_key = Project._dev_suggest_key(project.name)

    Task = env['project.task'].with_context(active_test=False, tracking_disable=True)
    tasks = Task.search([('project_id', '!=', False)], order='id')
    tasks._dev_assign_keys()
    for task in Task.search([('dev_assignee_id', '=', False), ('user_ids', '!=', False)]):
        task.dev_assignee_id = task.user_ids[:1]
    for task in Task.search([('dev_reporter_id', '=', False)]):
        task.dev_reporter_id = task.create_uid
    env.flush_all()
