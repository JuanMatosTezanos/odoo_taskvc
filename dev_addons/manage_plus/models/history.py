# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ManageHistory(models.Model):
    _inherit = 'manage.history'

    tasks = fields.One2many(string="Issues")
    bug_count = fields.Integer(compute='_compute_progress')
    progress = fields.Float(compute='_compute_progress', help="Percentage of finished issues")

    @api.depends('tasks.state', 'tasks.issue_type')
    def _compute_progress(self):
        for history in self:
            issues = history.tasks
            done = len(issues.filtered(lambda i: i.state == 'done'))
            history.bug_count = len(issues.filtered(lambda i: i.issue_type == 'bug'))
            history.progress = (done / len(issues) * 100.0) if issues else 0.0
