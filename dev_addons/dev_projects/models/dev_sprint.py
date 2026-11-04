# -*- coding: utf-8 -*-
from collections import Counter
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

SPRINT_STATES = [
    ('planned', 'Planned'),
    ('running', 'Running'),
    ('closed', 'Closed'),
]


class DevSprint(models.Model):
    _name = 'dev.sprint'
    _description = 'Sprint'
    _inherit = ['mail.thread']
    _order = 'start_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    goal = fields.Char(string="Sprint Goal", tracking=True)
    description = fields.Text()
    project_id = fields.Many2one('project.project', string="Project", required=True,
                                 index=True, ondelete='cascade', tracking=True)
    active = fields.Boolean(default=True)
    # Started and completed by hand, like in Jira, instead of following the calendar.
    state = fields.Selection(SPRINT_STATES, string="Status", default='planned', required=True,
                             index=True, tracking=True, copy=False)
    start_date = fields.Datetime(tracking=True)
    duration = fields.Integer(default=14, help="Length of the sprint in days", tracking=True)
    # start + duration, but set to the real end when completed early.
    end_date = fields.Datetime(compute='_compute_end_date', store=True, readonly=False, tracking=True)

    task_ids = fields.One2many('project.task', 'dev_sprint_id', string="Issues")
    item_count = fields.Integer(string="Issue Count", compute='_compute_counts')
    done_count = fields.Integer(string="Done Issues", compute='_compute_counts')
    planned_points = fields.Integer(string="Planned Points", compute='_compute_counts')
    done_points = fields.Integer(string="Done Points", compute='_compute_counts')
    progress = fields.Float(compute='_compute_counts', help="Percentage of finished issues")

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for sprint in self:
            if sprint.start_date and sprint.duration > 0:
                sprint.end_date = sprint.start_date + timedelta(days=sprint.duration)
            else:
                sprint.end_date = sprint.start_date

    @api.depends('task_ids.dev_status', 'task_ids.dev_story_points')
    def _compute_counts(self):
        for sprint in self:
            # Archived (completed) issues still count: they were done in this sprint.
            issues = sprint.with_context(active_test=False).task_ids
            done = issues.filtered(lambda i: i.dev_status == 'done')
            sprint.item_count = len(issues)
            sprint.done_count = len(done)
            sprint.progress = (len(done) / len(issues) * 100.0) if issues else 0.0
            sprint.planned_points = sum(issues.mapped('dev_story_points'))
            sprint.done_points = sum(done.mapped('dev_story_points'))

    @api.constrains('duration')
    def _check_duration(self):
        if any(sprint.duration <= 0 for sprint in self):
            raise ValidationError(_("A sprint must last at least one day."))

    @api.constrains('state', 'project_id')
    def _check_one_running(self):
        for sprint in self.filtered(lambda s: s.state == 'running'):
            others = self.search_count([
                ('id', '!=', sprint.id), ('project_id', '=', sprint.project_id.id),
                ('state', '=', 'running'),
            ])
            if others:
                raise ValidationError(_(
                    "Project %s already has a running sprint. Complete it first.",
                    sprint.project_id.name))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'name' in fields_list and not res.get('name'):
            res['name'] = self._dev_next_name(res.get('project_id'))
        return res

    @api.model
    def _dev_next_name(self, project_id, offset=1):
        existing = self.with_context(active_test=False).search_count(
            [('project_id', '=', project_id or False)])
        return _("Sprint %s", existing + offset)

    @api.model_create_multi
    def create(self, vals_list):
        added = Counter()
        for vals in vals_list:
            if not vals.get('name'):
                project_id = vals.get('project_id')
                added[project_id] += 1
                vals['name'] = self._dev_next_name(project_id, added[project_id])
        return super().create(vals_list)

    @api.onchange('project_id')
    def _onchange_project_id_name(self):
        # "Sprint 1" was computed before the project was picked: renumber.
        if self.project_id and (not self.name or self.name.startswith(_("Sprint "))):
            self.name = self._dev_next_name(self.project_id.id)

    def action_start(self):
        for sprint in self:
            if sprint.state != 'planned':
                raise UserError(_("Only planned sprints can be started."))
            vals = {'state': 'running'}
            now = fields.Datetime.now()
            if not sprint.start_date or sprint.start_date > now:
                vals['start_date'] = now
            sprint.write(vals)

    def action_open_complete_wizard(self):
        self.ensure_one()
        if self.state != 'running':
            raise UserError(_("Only running sprints can be completed."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Complete %s", self.name),
            'res_model': 'dev.sprint.complete',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sprint_id': self.id},
        }

    def _complete(self, target_sprint=None):
        """Close the sprint and move unfinished issues to `target_sprint` (or the backlog)."""
        self.ensure_one()
        all_issues = self.with_context(active_test=False).task_ids
        open_issues = all_issues.filtered(lambda i: i.dev_status != 'done')
        open_issues.write({'dev_sprint_id': target_sprint.id if target_sprint else False})
        self.write({'state': 'closed', 'end_date': fields.Datetime.now()})
        where = target_sprint.name if target_sprint else _("the backlog")
        # _message_log, not message_post: posting fails for users without an email address.
        self._message_log(body=_(
            "Sprint completed: %(done)s issue(s) done, %(open)s moved to %(where)s.",
            done=len(all_issues) - len(open_issues), open=len(open_issues), where=where))

    def action_view_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_projects.action_board')
        action.update({
            'domain': [('dev_sprint_id', '=', self.id)],
            'context': {'default_project_id': self.project_id.id,
                        'default_dev_sprint_id': self.id, 'dev_board': True},
            'display_name': self.name,
        })
        return action


class DevSprintComplete(models.TransientModel):
    _name = 'dev.sprint.complete'
    _description = 'Complete Sprint'

    sprint_id = fields.Many2one('dev.sprint', string="Completed Sprint", required=True, ondelete='cascade')
    project_id = fields.Many2one(related='sprint_id.project_id')
    done_count = fields.Integer(compute='_compute_counts')
    open_count = fields.Integer(compute='_compute_counts')
    destination = fields.Selection(
        [('sprint', 'Next sprint'), ('backlog', 'Backlog')],
        string="Move unfinished issues to", required=True,
        default=lambda self: 'sprint' if self._next_sprint() else 'backlog')
    target_sprint_id = fields.Many2one(
        'dev.sprint', string="Next Sprint",
        domain="[('project_id', '=', project_id), ('state', '=', 'planned')]",
        default=lambda self: self._next_sprint())

    def _next_sprint(self):
        sprint = self.env['dev.sprint'].browse(self.env.context.get('default_sprint_id'))
        if not sprint.exists():
            return self.env['dev.sprint']
        return self.env['dev.sprint'].search([
            ('project_id', '=', sprint.project_id.id), ('state', '=', 'planned'),
        ], order='start_date, id', limit=1)

    @api.depends('sprint_id')
    def _compute_counts(self):
        for wizard in self:
            issues = wizard.sprint_id.task_ids
            wizard.open_count = len(issues.filtered(lambda i: i.dev_status != 'done'))
            wizard.done_count = len(issues) - wizard.open_count

    def action_confirm(self):
        self.ensure_one()
        if self.open_count and self.destination == 'sprint' and not self.target_sprint_id:
            raise UserError(_("Pick the sprint that receives the unfinished issues."))
        target = self.target_sprint_id if self.destination == 'sprint' else None
        self.sprint_id._complete(target)
        return {'type': 'ir.actions.act_window_close'}
