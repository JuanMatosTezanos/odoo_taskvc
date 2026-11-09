# -*- coding: utf-8 -*-
from collections import Counter
from datetime import timedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .project_task import ISSUE_TYPES

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
                                 domain=[('dev_is_software', '=', True)],
                                 index=True, ondelete='cascade', tracking=True)
    milestone_id = fields.Many2one(
        'project.milestone', string="Milestone", index=True, tracking=True, ondelete='set null',
        domain="[('project_id', '=', project_id), ('is_reached', '=', False)]",
        help="The goal this sprint works towards. Issues added to the sprint get this milestone.")
    active = fields.Boolean(default=True)
    # Started and completed by hand, like in Jira, instead of following the calendar.
    state = fields.Selection(SPRINT_STATES, string="Status", default='planned', required=True,
                             index=True, tracking=True, copy=False)
    start_date = fields.Datetime(tracking=True)
    duration = fields.Integer(default=lambda self: self._default_duration(),
                              help="Length of the sprint in days", tracking=True)
    # start + duration, but set to the real end when completed early.
    end_date = fields.Datetime(compute='_compute_end_date', store=True, readonly=False, tracking=True)

    # Sub-tasks follow their parent and count inside it, not on their own.
    task_ids = fields.One2many('project.task', 'dev_sprint_id', string="Issues",
                               domain=[('display_in_project', '=', True)])
    item_count = fields.Integer(string="Issue Count", compute='_compute_counts')
    done_count = fields.Integer(string="Done Issues", compute='_compute_counts')
    planned_points = fields.Integer(string="Planned Points", compute='_compute_counts')
    done_points = fields.Integer(string="Done Points", compute='_compute_counts')
    progress = fields.Float(compute='_compute_counts', help="Percentage of finished issues")

    # Recap: a snapshot taken when the sprint is completed (what was in it, what
    # got finished, what moved on), plus the team's own summary of the sprint.
    # A snapshot, because unfinished issues leave the sprint when it completes.
    recap_notes = fields.Html(string="Sprint Summary")
    recap_issue_count = fields.Integer(string="Issues at the End", readonly=True, copy=False)
    recap_done_count = fields.Integer(string="Issues Finished", readonly=True, copy=False)
    recap_planned_points = fields.Integer(string="Points at the End", readonly=True, copy=False)
    recap_done_points = fields.Integer(string="Points Finished", readonly=True, copy=False)
    recap_moved_count = fields.Integer(string="Unfinished Issues Moved", readonly=True, copy=False)
    recap_moved_sprint_id = fields.Many2one('dev.sprint', string="Moved To Sprint", readonly=True,
                                            copy=False, ondelete='set null')
    recap_moved_to = fields.Char(string="Moved To", compute='_compute_recap')
    recap_progress = fields.Float(string="Finished", compute='_compute_recap')
    # active_test off: finished issues are often archived (Complete > Archive).
    recap_done_task_ids = fields.Many2many(
        'project.task', 'dev_sprint_recap_done_rel', 'sprint_id', 'task_id',
        string="Finished Issues", readonly=True, copy=False, context={'active_test': False})
    recap_moved_task_ids = fields.Many2many(
        'project.task', 'dev_sprint_recap_moved_rel', 'sprint_id', 'task_id',
        string="Unfinished Issues", readonly=True, copy=False, context={'active_test': False})
    recap_line_ids = fields.One2many('dev.sprint.recap.line', 'sprint_id', readonly=True, copy=False)
    recap_type_line_ids = fields.One2many('dev.sprint.recap.line', 'sprint_id', string="Finished by Type",
                                          domain=[('kind', '=', 'type')], readonly=True)
    recap_component_line_ids = fields.One2many('dev.sprint.recap.line', 'sprint_id',
                                               string="Finished by Component",
                                               domain=[('kind', '=', 'component')], readonly=True)
    recap_person_line_ids = fields.One2many('dev.sprint.recap.line', 'sprint_id', string="Finished by Person",
                                            domain=[('kind', '=', 'person')], readonly=True)

    def _default_duration(self):
        # Settings > Project > Dev Projects > Default Sprint Length.
        value = self.env['ir.config_parameter'].sudo().get_param('dev_projects.sprint_duration', '14')
        try:
            return max(int(value), 1)
        except ValueError:
            return 14

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

    @api.depends('recap_done_count', 'recap_issue_count', 'recap_moved_count', 'recap_moved_sprint_id')
    def _compute_recap(self):
        for sprint in self:
            sprint.recap_progress = (sprint.recap_done_count / sprint.recap_issue_count * 100.0) \
                if sprint.recap_issue_count else 0.0
            if not sprint.recap_moved_count:
                sprint.recap_moved_to = False
            else:
                sprint.recap_moved_to = sprint.recap_moved_sprint_id.name or _("Backlog")

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

    @api.constrains('milestone_id', 'project_id')
    def _check_milestone_project(self):
        for sprint in self:
            if sprint.milestone_id and sprint.milestone_id.project_id != sprint.project_id:
                raise ValidationError(_(
                    "Sprint %(sprint)s: milestone %(milestone)s belongs to project %(other)s, not %(project)s.",
                    sprint=sprint.name, milestone=sprint.milestone_id.name,
                    other=sprint.milestone_id.project_id.name, project=sprint.project_id.name))

    @api.onchange('project_id')
    def _onchange_project_id_milestone(self):
        for sprint in self:
            if sprint.milestone_id.project_id != sprint.project_id:
                sprint.milestone_id = False

    def write(self, vals):
        res = super().write(vals)
        if vals.get('milestone_id'):
            # Issues already in the sprint join its milestone (unless they have one).
            self.with_context(active_test=False).task_ids._dev_fill_milestone_from_sprint()
        return res

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
        return self._dev_reload_project_form()

    def _dev_reload_project_form(self):
        """Opened from a project's Sprints tab (a pop-up over the project): reload
        the project behind it, so "Running Sprint" shows the change at once."""
        if self.env.context.get('dev_reload_project'):
            return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
        return False

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
            'context': {'default_sprint_id': self.id,
                        'dev_reload_project': self.env.context.get('dev_reload_project', False)},
        }

    def _complete(self, target_sprint=None):
        """Close the sprint and move unfinished issues to `target_sprint` (or the backlog)."""
        self.ensure_one()
        all_issues = self.with_context(active_test=False).task_ids
        open_issues = all_issues.filtered(lambda i: i.dev_status != 'done')
        # Snapshot first: the unfinished issues are about to leave the sprint.
        self._dev_take_recap(all_issues, open_issues, target_sprint)
        open_issues.write({'dev_sprint_id': target_sprint.id if target_sprint else False})
        self.write({'state': 'closed', 'end_date': fields.Datetime.now()})
        where = target_sprint.name if target_sprint else _("the backlog")
        # _message_log, not message_post: posting fails for users without an email address.
        self._message_log(body=_(
            "Sprint completed: %(done)s issue(s) done, %(open)s moved to %(where)s.",
            done=len(all_issues) - len(open_issues), open=len(open_issues), where=where))

    def _dev_take_recap(self, issues, open_issues, target_sprint=None):
        """Store what the sprint achieved: totals, finished and unfinished issues,
        and what was finished per type, component and person."""
        self.ensure_one()
        done = issues - open_issues
        lines = []
        for issue_type, _label in ISSUE_TYPES:
            group = done.filtered(lambda i: i.dev_issue_type == issue_type)
            if group:
                lines.append({'kind': 'type', 'issue_type': issue_type, 'issue_count': len(group),
                              'points': sum(group.mapped('dev_story_points'))})
        for kind, fname in (('component', 'dev_module_id'), ('person', 'dev_assignee_id')):
            # Each component / person, then the issues without one.
            for record in list(done.mapped(fname)) + [self.env[done._fields[fname].comodel_name]]:
                group = done.filtered(lambda i: i[fname] == record)
                if not group:
                    continue
                lines.append({'kind': kind, 'module_id' if kind == 'component' else 'user_id': record.id,
                              'label': record.display_name if record else False,
                              'issue_count': len(group), 'points': sum(group.mapped('dev_story_points'))})
        self.recap_line_ids.unlink()
        self.write({
            'recap_issue_count': len(issues),
            'recap_done_count': len(done),
            'recap_planned_points': sum(issues.mapped('dev_story_points')),
            'recap_done_points': sum(done.mapped('dev_story_points')),
            'recap_moved_count': len(open_issues),
            'recap_moved_sprint_id': target_sprint.id if target_sprint and open_issues else False,
            'recap_done_task_ids': [Command.set(done.ids)],
            'recap_moved_task_ids': [Command.set(open_issues.ids)],
            'recap_line_ids': [Command.create(vals) for vals in lines],
        })

    def action_dev_open_recap(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s Recap", self.name),
            'res_model': 'dev.sprint',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('dev_addons.sprint_recap_form').id, 'form')],
            'target': 'new',
            'context': {'dev_reload_project': self.env.context.get('dev_reload_project', False)},
        }

    def action_dev_recap_done(self):
        # The summary is saved before this runs (Odoo saves the record first).
        return self._dev_reload_project_form() or {'type': 'ir.actions.act_window_close'}

    def action_view_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_addons.action_board')
        action.update({
            'domain': [('dev_sprint_id', '=', self.id), ('display_in_project', '=', True)],
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
            issues = wizard.sprint_id.with_context(active_test=False).task_ids
            wizard.open_count = len(issues.filtered(lambda i: i.dev_status != 'done'))
            wizard.done_count = len(issues) - wizard.open_count

    def action_confirm(self):
        self.ensure_one()
        if self.open_count and self.destination == 'sprint' and not self.target_sprint_id:
            raise UserError(_("Pick the sprint that receives the unfinished issues."))
        target = self.target_sprint_id if self.destination == 'sprint' else None
        self.sprint_id._complete(target)
        # Show the recap right away; "Save" there reloads the screen behind it.
        return self.sprint_id.action_dev_open_recap()


class DevSprintRecapLine(models.Model):
    """One row of a sprint recap: what was finished for one issue type,
    component or person."""
    _name = 'dev.sprint.recap.line'
    _description = 'Sprint Recap Line'
    _order = 'kind, issue_count desc, id'

    sprint_id = fields.Many2one('dev.sprint', required=True, index=True, ondelete='cascade')
    kind = fields.Selection([('type', 'Type'), ('component', 'Component'), ('person', 'Person')],
                            required=True)
    issue_type = fields.Selection(ISSUE_TYPES, string="Type")
    module_id = fields.Many2one('dev.module', string="Component", ondelete='set null')
    user_id = fields.Many2one('res.users', string="Person", ondelete='set null')
    label = fields.Char(help="Name at the time of the recap, kept if the component or user is deleted.")
    name = fields.Char(compute='_compute_name')
    issue_count = fields.Integer(string="Issues Finished")
    points = fields.Integer(string="Points Finished")

    @api.depends('kind', 'issue_type', 'module_id', 'user_id', 'label')
    def _compute_name(self):
        types = dict(self._fields['issue_type']._description_selection(self.env))
        for line in self:
            if line.kind == 'type':
                line.name = types.get(line.issue_type, '')
            elif line.kind == 'component':
                line.name = line.module_id.name or line.label or _("No component")
            else:
                line.name = line.user_id.name or line.label or _("Unassigned")
