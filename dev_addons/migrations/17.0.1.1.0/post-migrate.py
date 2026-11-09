# -*- coding: utf-8 -*-
"""17.0.1.1.0: Milestones replace Histories.

Each history becomes a milestone of the same project, with its name and
description, and its issues move to that milestone. The old dev_history table
is still there at this point; Odoo removes it right after this script.
"""
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import plaintext2html

from odoo.addons.dev_addons.hooks import enable_milestones

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    enable_milestones(env)

    cr.execute("SELECT to_regclass('dev_history')")
    if not cr.fetchone()[0]:
        return
    cr.execute("SELECT id, name, description, project_id FROM dev_history ORDER BY id")
    histories = cr.fetchall()
    Task = env['project.task'].with_context(active_test=False)
    for history_id, name, description, project_id in histories:
        milestone = env['project.milestone'].create({
            'name': name,
            'project_id': project_id,
            'description': plaintext2html(description) if description else False,
        })
        cr.execute("SELECT id FROM project_task WHERE dev_history_id = %s", [history_id])
        tasks = Task.browse([row[0] for row in cr.fetchall()])
        tasks.filtered(lambda t: not t.milestone_id and t.project_id.id == project_id).write(
            {'milestone_id': milestone.id})
        _logger.info("History %r is now milestone %s (%s issues)", name, milestone.id, len(tasks))
