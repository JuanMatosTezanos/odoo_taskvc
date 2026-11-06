# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ProjectMilestone(models.Model):
    """Milestones of software projects: a goal with a deadline that groups
    sprints and issues.

    These are Odoo's own milestones, so the Project app shows the same ones.
    Dev Projects adds a description, sprints, progress and a Complete button.
    """
    _inherit = 'project.milestone'

    is_reached = fields.Boolean(tracking=True)
    description = fields.Html()
    dev_is_software = fields.Boolean(related='project_id.dev_is_software')
    dev_sprint_ids = fields.One2many('dev.sprint', 'milestone_id', string="Sprints")
    dev_sprint_count = fields.Integer(string="Sprint Count", compute='_compute_dev_progress')
    dev_issue_count = fields.Integer(string="Issues", compute='_compute_dev_progress')
    dev_done_count = fields.Integer(string="Done Issues", compute='_compute_dev_progress')
    dev_open_count = fields.Integer(string="Open Issues", compute='_compute_dev_progress')
    dev_bug_count = fields.Integer(string="Bugs", compute='_compute_dev_progress')
    dev_planned_points = fields.Integer(string="Planned Points", compute='_compute_dev_progress')
    dev_done_points = fields.Integer(string="Done Points", compute='_compute_dev_progress')
    dev_progress = fields.Float(string="Progress", compute='_compute_dev_progress',
                                help="Percentage of finished issues")
    dev_technology_ids = fields.Many2many(
        'dev.technology', string="Technologies", compute='_compute_dev_progress',
        help="Technologies used by the issues of this milestone.")

    @api.depends('task_ids.dev_status', 'task_ids.dev_story_points', 'task_ids.dev_issue_type',
                 'task_ids.dev_technology_ids', 'dev_sprint_ids')
    def _compute_dev_progress(self):
        for milestone in self:
            # Archived (completed) issues still count: they were done for this milestone.
            issues = milestone.with_context(active_test=False).task_ids
            done = issues.filtered(lambda i: i.dev_status == 'done')
            milestone.dev_sprint_count = len(milestone.dev_sprint_ids)
            milestone.dev_issue_count = len(issues)
            milestone.dev_done_count = len(done)
            milestone.dev_open_count = len(issues) - len(done)
            milestone.dev_bug_count = len(issues.filtered(lambda i: i.dev_issue_type == 'bug'))
            milestone.dev_planned_points = sum(issues.mapped('dev_story_points'))
            milestone.dev_done_points = sum(done.mapped('dev_story_points'))
            milestone.dev_progress = (len(done) / len(issues) * 100.0) if issues else 0.0
            milestone.dev_technology_ids = issues.dev_technology_ids

    def action_dev_complete(self):
        self.write({'is_reached': True})

    def action_dev_reopen(self):
        self.write({'is_reached': False})

    def action_dev_view_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_projects.action_board')
        action.update({
            'domain': [('milestone_id', '=', self.id)],
            'context': {'default_project_id': self.project_id.id, 'default_milestone_id': self.id,
                        'dev_board': True},
            'display_name': self.name,
        })
        return action

    def action_dev_view_sprints(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_projects.action_sprint')
        action.update({
            'domain': [('milestone_id', '=', self.id)],
            'context': {'default_project_id': self.project_id.id, 'default_milestone_id': self.id},
            'display_name': _("%s - Sprints", self.name),
        })
        return action
