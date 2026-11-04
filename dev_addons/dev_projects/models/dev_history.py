# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DevHistory(models.Model):
    """A user history / epic: a feature of a project that groups issues."""
    _name = 'dev.history'
    _description = 'History'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(required=True, tracking=True)
    description = fields.Text()
    color = fields.Integer()
    project_id = fields.Many2one('project.project', string="Project", required=True,
                                 index=True, ondelete='cascade', tracking=True)
    task_ids = fields.One2many('project.task', 'dev_history_id', string="Issues")
    task_count = fields.Integer(string="Issue Count", compute='_compute_progress')
    bug_count = fields.Integer(string="Bug Count", compute='_compute_progress')
    progress = fields.Float(compute='_compute_progress', help="Percentage of finished issues")
    used_technology_ids = fields.Many2many(
        'dev.technology', string="Used Technologies", compute='_compute_used_technologies')

    @api.depends('task_ids.dev_status', 'task_ids.dev_issue_type')
    def _compute_progress(self):
        for history in self:
            # Archived (completed) issues still count as done work.
            issues = history.with_context(active_test=False).task_ids
            done = len(issues.filtered(lambda i: i.dev_status == 'done'))
            history.task_count = len(issues)
            history.bug_count = len(issues.filtered(lambda i: i.dev_issue_type == 'bug'))
            history.progress = (done / len(issues) * 100.0) if issues else 0.0

    @api.depends('task_ids.dev_technology_ids')
    def _compute_used_technologies(self):
        for history in self:
            history.used_technology_ids = history.task_ids.dev_technology_ids
