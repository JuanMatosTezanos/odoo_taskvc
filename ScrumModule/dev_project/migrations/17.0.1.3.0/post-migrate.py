# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Sprints completed before recaps existed get one from what they still
    hold: their finished issues. (Their unfinished issues already moved on,
    so the recap of those older sprints only lists what was finished.)"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    sprints = env['dev.sprint'].with_context(active_test=False).search([
        ('state', '=', 'closed'), ('recap_issue_count', '=', 0),
    ])
    for sprint in sprints:
        issues = sprint.with_context(active_test=False).task_ids
        done = issues.filtered(lambda i: i.dev_status == 'done')
        sprint._dev_take_recap(done, env['project.task'])
