# -*- coding: utf-8 -*-
from odoo import api, fields, models

# The four fixed statuses of the base module now act as categories: every
# board column (stage) belongs to one, so filters, buttons and dates keep working.
from odoo.addons.manage.models.models import TASK_STATES


class ManageStage(models.Model):
    _name = 'manage.stage'
    _description = 'Board Column'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        TASK_STATES, string="Status Category", required=True, default='todo',
        help="What this column means for reporting and dates: an issue moved to a "
             "'Done' column gets its end date, an 'In Progress' one its start date.")
    fold = fields.Boolean(string="Folded on Board")
    wip_limit = fields.Integer(
        string="WIP Limit",
        help="Maximum number of issues of one project and sprint in this column. 0 means no limit.")
    project_ids = fields.Many2many(
        'manage.project', string="Projects",
        help="Leave empty to use this column on every project.")
    active = fields.Boolean(default=True)

    @api.depends('name', 'wip_limit')
    def _compute_display_name(self):
        # Shown as the board column title, so the limit is visible there.
        for stage in self:
            stage.display_name = (f"{stage.name} (max {stage.wip_limit})"
                                  if stage.wip_limit else stage.name)

    @api.model
    def _for_state(self, state, project=None):
        """First column of a status category, preferring the project's own columns."""
        domain = [('state', '=', state)]
        if project:
            domain += ['|', ('project_ids', '=', False), ('project_ids', 'in', project.id)]
        return self.search(domain, limit=1)
