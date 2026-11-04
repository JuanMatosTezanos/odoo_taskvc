# -*- coding: utf-8 -*-
from collections import Counter

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

SPRINT_STATES = [
    ('planned', 'Planned'),
    ('running', 'Running'),
    ('closed', 'Closed'),
]


class ManageSprint(models.Model):
    _name = 'manage.sprint'
    _inherit = ['manage.sprint', 'mail.thread']
    _order = 'start_date desc, id desc'

    # In the base module `active` was computed from the dates, which made Odoo
    # archive (hide) every sprint that was not running. It is a plain archive
    # flag again; whether a sprint is running lives in `state`.
    active = fields.Boolean(default=True, compute=None, readonly=False, store=True)
    # Sprints are started and completed by hand, like in Jira, instead of
    # following the calendar.
    state = fields.Selection(
        SPRINT_STATES, string="Status", default='planned', required=True,
        index=True, tracking=True, copy=False)

    name = fields.Char(tracking=True)
    goal = fields.Char(string="Sprint Goal", tracking=True)
    start_date = fields.Datetime(tracking=True)
    duration = fields.Integer(tracking=True)
    # Still start + duration, but set to the real end when completed early.
    end_date = fields.Datetime(readonly=False, tracking=True)

    tasks = fields.One2many(string="Issues")
    item_count = fields.Integer(string="Issue Count", compute='_compute_task_count')
    done_count = fields.Integer(string="Done Issues", compute='_compute_task_count')
    planned_points = fields.Integer(string="Planned Points", compute='_compute_task_count')
    done_points = fields.Integer(string="Done Points", compute='_compute_task_count')

    # Same name as the base method, so it replaces it.
    @api.depends('tasks.state', 'tasks.story_points')
    def _compute_task_count(self):
        for sprint in self:
            # Archived (completed) issues still count: they were done in this sprint.
            issues = sprint.with_context(active_test=False).tasks
            done = issues.filtered(lambda i: i.state == 'done')
            sprint.task_count = sprint.item_count = len(issues)
            sprint.done_count = len(done)
            sprint.progress = (len(done) / len(issues) * 100.0) if issues else 0.0
            sprint.planned_points = sum(issues.mapped('story_points'))
            sprint.done_points = sum(done.mapped('story_points'))

    @api.constrains('duration')
    def _check_duration(self):
        if any(sprint.duration <= 0 for sprint in self):
            raise ValidationError(_("A sprint must last at least one day."))

    @api.constrains('state', 'project')
    def _check_one_running(self):
        for sprint in self.filtered(lambda s: s.state == 'running' and s.project):
            others = self.search_count([
                ('id', '!=', sprint.id), ('project', '=', sprint.project.id),
                ('state', '=', 'running'),
            ])
            if others:
                raise ValidationError(_(
                    "Project %s already has a running sprint. Complete it first.",
                    sprint.project.name))

    @api.model_create_multi
    def create(self, vals_list):
        # Give unnamed sprints a name ("Sprint 3") so they are readable in lists.
        added = Counter()
        for vals in vals_list:
            if not vals.get('name'):
                project_id = vals.get('project') or False
                existing = self.with_context(active_test=False).search_count(
                    [('project', '=', project_id)])
                added[project_id] += 1
                vals['name'] = _("Sprint %s", existing + added[project_id])
        return super().create(vals_list)

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
            'res_model': 'manage.sprint.complete',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sprint_id': self.id},
        }

    def _complete(self, target_sprint=None):
        """Close the sprint and move unfinished issues to `target_sprint` (or the backlog)."""
        self.ensure_one()
        all_issues = self.with_context(active_test=False).tasks
        open_issues = all_issues.filtered(lambda i: i.state != 'done')
        done_count = len(all_issues) - len(open_issues)
        open_issues.write({'sprint': target_sprint.id if target_sprint else False})
        self.write({'state': 'closed', 'end_date': fields.Datetime.now()})
        where = target_sprint.name if target_sprint else _("the backlog")
        # _message_log, not message_post: posting fails for users without an
        # email address ("Unable to send message"), which blocked completing.
        self._message_log(body=_(
            "Sprint completed: %(done)s issue(s) done, %(open)s moved to %(where)s.",
            done=done_count, open=len(open_issues), where=where))

    @api.model
    def cron_update_sprints(self):
        # Sprints are started and completed by hand now; the base cron is
        # switched off in data, and this keeps it harmless if re-enabled.
        return True


class ManageSprintComplete(models.TransientModel):
    _name = 'manage.sprint.complete'
    _description = 'Complete Sprint'

    sprint_id = fields.Many2one('manage.sprint', string="Completed Sprint", required=True, ondelete='cascade')
    project_id = fields.Many2one(related='sprint_id.project')
    done_count = fields.Integer(compute='_compute_counts')
    open_count = fields.Integer(compute='_compute_counts')
    destination = fields.Selection(
        [('sprint', 'Next sprint'), ('backlog', 'Backlog')],
        string="Move unfinished issues to", required=True,
        default=lambda self: self._default_destination())
    target_sprint_id = fields.Many2one(
        'manage.sprint', string="Next Sprint",
        domain="[('project', '=', project_id), ('state', '=', 'planned')]",
        default=lambda self: self._next_sprint())

    def _next_sprint(self):
        sprint = self.env['manage.sprint'].browse(self.env.context.get('default_sprint_id'))
        if not sprint.project:
            return self.env['manage.sprint']
        return self.env['manage.sprint'].search([
            ('project', '=', sprint.project.id), ('state', '=', 'planned'),
        ], order='start_date, id', limit=1)

    def _default_destination(self):
        return 'sprint' if self._next_sprint() else 'backlog'

    @api.depends('sprint_id')
    def _compute_counts(self):
        for wizard in self:
            issues = wizard.sprint_id.tasks
            wizard.open_count = len(issues.filtered(lambda i: i.state != 'done'))
            wizard.done_count = len(issues) - wizard.open_count

    def action_confirm(self):
        self.ensure_one()
        if self.open_count and self.destination == 'sprint' and not self.target_sprint_id:
            raise UserError(_("Pick the sprint that receives the unfinished issues."))
        target = self.target_sprint_id if self.destination == 'sprint' else None
        self.sprint_id._complete(target)
        return {'type': 'ir.actions.act_window_close'}
