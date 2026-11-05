# -*- coding: utf-8 -*-
from odoo import api, fields, models

# What a board column means for reporting, dates and the Done state.
DEV_STATUSES = [
    ('todo', 'To Do'),
    ('in_progress', 'In Progress'),
    ('review', 'In Review'),
    ('done', 'Done'),
]


class ProjectTaskType(models.Model):
    """Project stages are the board columns."""
    _inherit = 'project.task.type'

    dev_category = fields.Selection(
        DEV_STATUSES, string="Status Category", required=True, default='todo',
        help="What this column means: an issue moved to a 'Done' column is marked done "
             "(also in the Project app), an 'In Progress' one gets its start date.")
    dev_wip_limit = fields.Integer(
        string="WIP Limit",
        help="Maximum number of issues of one project and sprint in this column. 0 means no limit. "
             "Not applied to Done columns.")

    @api.model
    def _dev_guess_category(self, name):
        """Category for an existing stage from its name (used once, on install)."""
        name = (name or '').lower()
        if any(word in name for word in ('done', 'complete', 'closed', 'finished', 'cancel')):
            return 'done'
        if any(word in name for word in ('review', 'test', 'qa', 'validat', 'approv')):
            return 'review'
        if any(word in name for word in ('progress', 'doing', 'develop', 'work')):
            return 'in_progress'
        return 'todo'

    def _dev_for_category(self, category, project):
        """First column of a status category in a project."""
        return self.search([
            ('dev_category', '=', category), ('project_ids', 'in', project.id),
        ], order='sequence, id', limit=1)

    @api.model
    def _dev_default_stages(self):
        """The four default columns linked to every new project."""
        return (self.env.ref('dev_projects.stage_todo', raise_if_not_found=False)
                | self.env.ref('dev_projects.stage_in_progress', raise_if_not_found=False)
                | self.env.ref('dev_projects.stage_review', raise_if_not_found=False)
                | self.env.ref('dev_projects.stage_done', raise_if_not_found=False))
