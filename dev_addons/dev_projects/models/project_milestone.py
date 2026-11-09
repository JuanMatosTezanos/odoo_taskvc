# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# 1.0, 1.2.0, v2.0.1, 2.1.0-beta
VERSION_RE = re.compile(r'^[vV]?\d+(\.\d+){0,3}(-[0-9A-Za-z.]+)?$')


class ProjectMilestone(models.Model):
    """Milestones of software projects: a goal with a deadline that groups
    sprints and issues.

    These are Odoo's own milestones, so the Project app shows the same ones.
    Dev Projects adds a version, a description, sprints, progress and a
    Complete button.
    """
    _inherit = 'project.milestone'

    is_reached = fields.Boolean(tracking=True)
    description = fields.Html()
    dev_version = fields.Char(
        string="Version", tracking=True,
        help="The version this milestone ships as, e.g. 1.2.0 or v2.0.1.")
    dev_is_software = fields.Boolean(related='project_id.dev_is_software')
    # The milestone's issues without sub-tasks (those count inside their parent).
    dev_issue_ids = fields.One2many('project.task', 'milestone_id', string="Milestone Issues",
                                    domain=[('display_in_project', '=', True)])
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

    @api.depends('dev_issue_ids.dev_status', 'dev_issue_ids.dev_story_points', 'dev_issue_ids.dev_issue_type',
                 'dev_issue_ids.dev_technology_ids', 'dev_sprint_ids')
    def _compute_dev_progress(self):
        for milestone in self:
            # Archived (completed) issues still count: they were done for this milestone.
            issues = milestone.with_context(active_test=False).dev_issue_ids
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

    @api.model
    def _dev_clean_version(self, vals):
        if vals.get('dev_version'):
            vals['dev_version'] = vals['dev_version'].strip()
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._dev_clean_version(dict(vals)) for vals in vals_list])

    def write(self, vals):
        return super().write(self._dev_clean_version(dict(vals)))

    @api.constrains('dev_version')
    def _check_dev_version(self):
        for milestone in self:
            if milestone.dev_version and not VERSION_RE.match(milestone.dev_version):
                raise ValidationError(_(
                    "Version %s is not a version number. Use numbers separated by dots, "
                    "e.g. 1.0, 1.2.0 or v2.0.1 (a tag like 2.1.0-beta is fine too).",
                    milestone.dev_version))

    def action_dev_complete(self):
        self.write({'is_reached': True})

    def action_dev_reopen(self):
        self.write({'is_reached': False})

    def action_dev_view_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_projects.action_board')
        action.update({
            'domain': [('milestone_id', '=', self.id), ('display_in_project', '=', True)],
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
