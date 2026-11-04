# -*- coding: utf-8 -*-
import re

from odoo import Command, _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError, ValidationError

ISSUE_TYPES = [
    ('story', 'Story'),
    ('task', 'Task'),
    ('bug', 'Bug'),
    ('improvement', 'Improvement'),
]

SEVERITIES = [
    ('minor', 'Minor'),
    ('major', 'Major'),
    ('critical', 'Critical'),
    ('blocker', 'Blocker'),
]

# Old codes from before project keys existed: TSK_12, BUG_3, IMP_7.
LEGACY_CODE_RE = re.compile(r'^\s*(?:TSK|BUG|IMP)_?(\d+)\s*$', re.I)


class ManageTask(models.Model):
    """The single "issue" model: stories, tasks, bugs and improvements.

    The base module has three separate models (manage.task, manage.bug,
    manage.improvement), so they could not share a board, a backlog or keys.
    manage.task is now the one issue model with a type; old bugs and
    improvements are moved into it on install/upgrade (see hooks.py).
    """
    _name = 'manage.task'
    _description = 'Issue'
    _inherit = ['manage.task', 'mail.thread', 'mail.activity.mixin']
    _order = 'sequence, priority desc, id desc'
    _rec_names_search = ['name', 'key']

    issue_type = fields.Selection(
        ISSUE_TYPES, string="Type", required=True, default='task', tracking=True, index=True)
    key = fields.Char(readonly=True, copy=False, index=True,
                      help="Project key and number, e.g. WEB-42.")
    sequence = fields.Integer(default=10, help="Rank in the backlog (drag to reorder).")
    # Completed issues can be archived: kept for reference, hidden from the board.
    active = fields.Boolean(default=True, tracking=True)

    name = fields.Char(tracking=True)
    priority = fields.Selection(tracking=True)
    state = fields.Selection(tracking=True)
    stage_id = fields.Many2one(
        'manage.stage', string="Stage", tracking=True, index=True, ondelete='restrict',
        group_expand='_read_group_stage_ids',
        domain="['|', ('project_ids', '=', False), ('project_ids', 'in', project and [project] or [])]")
    history = fields.Many2one(tracking=True, domain="[('project', '=', project)]")
    # Was a read-only copy of history.project, so an issue could not belong to
    # a project without a history. It now follows the history but can be set.
    project = fields.Many2one(
        related=None, compute='_compute_project', store=True, readonly=False,
        index=True, tracking=True, default=lambda self: self._default_project())
    sprint = fields.Many2one(
        compute=None, store=True, readonly=False, index=True, tracking=True,
        domain="[('project', '=', project), ('state', '!=', 'closed')]")

    assignee = fields.Many2one(
        'res.partner', string="Assignee", tracking=True, index=True,
        domain=[('is_dev', '=', True)], default=lambda self: self._default_assignee())
    reporter_id = fields.Many2one(
        'res.users', string="Reporter", default=lambda self: self.env.user, tracking=True)
    developer = fields.Many2many(string="Team")
    severity = fields.Selection(SEVERITIES, default='minor', tracking=True)

    # fields.Datetime.now is UTC, which is how Odoo stores datetimes.
    definition_date = fields.Datetime(default=fields.Datetime.now)
    code = fields.Char(search='_search_code')
    date_deadline = fields.Date(string="Deadline", tracking=True)
    is_overdue = fields.Boolean(
        string="Overdue", compute='_compute_is_overdue', search='_search_is_overdue')
    story_points = fields.Integer(string="Story Points", help="Relative effort estimate.")

    _sql_constraints = [
        ('key_unique', 'unique(key)', "Issue keys must be unique."),
    ]

    # ------------------------------------------------------------------
    # Defaults and computes
    # ------------------------------------------------------------------

    def _default_project(self):
        # Opened from a project, or there is only one project: use it.
        if self.env.context.get('default_project'):
            return self.env.context['default_project']
        projects = self.env['manage.project'].search([], limit=2)
        return projects.id if len(projects) == 1 else False

    def _default_assignee(self):
        # Opened from a developer's smart button: assign to that developer.
        return self.env.context.get('current_developer') or False

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # Show every column on the board, even empty ones.
        project_id = self.env.context.get('default_project')
        search = []
        if project_id:
            search = ['|', ('project_ids', '=', False), ('project_ids', 'in', project_id)]
        return stages.search(search, order=order)

    @api.depends('history.project')
    def _compute_project(self):
        for issue in self:
            issue.project = issue.history.project or issue.project

    def _get_code(self):
        for issue in self:
            if issue.key:
                issue.code = issue.key
            else:
                issue.code = f"TSK_{issue.id}" if isinstance(issue.id, int) else False

    def _search_code(self, operator, value):
        if operator not in ('=', 'ilike', 'like', '=ilike', '=like') or not isinstance(value, str):
            raise UserError(_("Unsupported search on Code."))
        legacy = LEGACY_CODE_RE.match(value)
        if legacy:
            return ['|', ('key', operator, value), ('id', '=', int(legacy.group(1)))]
        return [('key', operator, value)]

    @api.depends('name', 'key')
    def _compute_display_name(self):
        for issue in self:
            issue.display_name = f"[{issue.code}] {issue.name}" if issue.code else issue.name

    @api.depends('date_deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for issue in self:
            issue.is_overdue = bool(
                issue.date_deadline and issue.state != 'done' and issue.date_deadline < today)

    def _search_is_overdue(self, operator, value):
        if operator not in ('=', '!='):
            raise UserError(_("Unsupported search on Overdue."))
        today = fields.Date.context_today(self)
        if (operator == '=') == bool(value):
            return [('date_deadline', '<', today), ('state', '!=', 'done')]
        return ['|', '|', ('date_deadline', '=', False),
                ('date_deadline', '>=', today), ('state', '=', 'done')]

    @api.onchange('project')
    def _onchange_project(self):
        for issue in self:
            if issue.history.project != issue.project:
                issue.history = False
            if issue.sprint.project != issue.project:
                issue.sprint = False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for issue in self:
            if issue.start_date and issue.end_date and issue.end_date < issue.start_date:
                raise ValidationError(_("%s: the end date cannot be before the start date.",
                                        issue.display_name))

    @api.constrains('project', 'history', 'sprint')
    def _check_project_consistency(self):
        for issue in self:
            if issue.history.project and issue.history.project != issue.project:
                raise ValidationError(_("%s: the history belongs to another project.",
                                        issue.display_name))
            if issue.sprint and issue.sprint.project != issue.project:
                if not issue.project:
                    raise ValidationError(_(
                        "%(issue)s: set a project before putting it in sprint %(sprint)s.",
                        issue=issue.display_name, sprint=issue.sprint.name))
                raise ValidationError(_(
                    "%(issue)s: sprint %(sprint)s belongs to project %(other)s, not %(project)s.",
                    issue=issue.display_name, sprint=issue.sprint.name,
                    other=issue.sprint.project.name or _("(none)"), project=issue.project.name))

    def _check_wip_limits(self):
        """Refuse to put more issues in a column than its WIP limit allows.

        Counted per project and sprint, like a board in Jira.
        """
        groups = {(i.stage_id, i.project, i.sprint) for i in self if i.stage_id.wip_limit}
        for stage, project, sprint in groups:
            count = self.search_count([
                ('stage_id', '=', stage.id),
                ('project', '=', project.id),
                ('sprint', '=', sprint.id),
            ])
            if count > stage.wip_limit:
                raise UserError(_(
                    "Column %(stage)s allows %(limit)s issues and would have %(count)s. "
                    "Finish something first or raise the WIP limit.",
                    stage=stage.name, limit=stage.wip_limit, count=count))

    # ------------------------------------------------------------------
    # Create / write: keep stage <-> status, dates, keys and team in sync
    # ------------------------------------------------------------------

    def _prepare_stage_vals(self, vals, project=None):
        """Fill in `state` from `stage_id`, or a `stage_id` matching `state`."""
        Stage = self.env['manage.stage']
        if vals.get('stage_id'):
            vals['state'] = Stage.browse(vals['stage_id']).state
        elif 'stage_id' not in vals and 'state' not in vals and not self:
            # New issue without stage or state: first "To Do" column.
            vals['stage_id'] = Stage._for_state('todo', project).id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        Project = self.env['manage.project']
        for vals in vals_list:
            if 'project' not in vals:
                # Set it here, before field defaults are applied: a default
                # project must not win over the project of the given history.
                if vals.get('history'):
                    vals['project'] = self.env['manage.history'].browse(vals['history']).project.id
                else:
                    vals['project'] = self._default_project()
            project = Project.browse(vals.get('project') or [])
            if not project and vals.get('history'):
                project = self.env['manage.history'].browse(vals['history']).project
            if self.env.context.get('manage_board') and 'sprint' not in vals and project:
                # Created on the Board: put it in the sprint the board shows.
                vals['sprint'] = project._get_running_sprint().id
            if not vals.get('stage_id') and vals.get('state'):
                vals['stage_id'] = self.env['manage.stage']._for_state(vals['state'], project).id
            self._prepare_stage_vals(vals, project)
            if vals.get('assignee'):
                vals.setdefault('developer', [])
                vals['developer'] = list(vals['developer']) + [Command.link(vals['assignee'])]
        records = super().create(vals_list)
        records._sync_state_dates(clear=False)
        records._assign_keys()
        records._check_wip_limits()
        return records

    def write(self, vals):
        vals = self._prepare_stage_vals(dict(vals))
        if vals.get('assignee'):
            # The assignee is always part of the team, so developer pages and
            # counters keep working.
            vals['developer'] = list(vals.get('developer', [])) + [Command.link(vals['assignee'])]
        res = super().write(vals)
        if 'state' in vals:
            if 'stage_id' not in vals:
                # A button or the base module set the status: move the card
                # to the first column of that status.
                for issue in self.filtered(lambda i: i.stage_id.state != i.state):
                    issue.stage_id = self.env['manage.stage']._for_state(issue.state, issue.project)
            # The kanban drag, statusbar and buttons all end up here.
            self._sync_state_dates(keep=set(vals))
        if 'project' in vals or 'history' in vals:
            self._assign_keys()
        if {'stage_id', 'project', 'sprint', 'history'} & set(vals):
            self._check_wip_limits()
        return res

    def _sync_state_dates(self, keep=(), clear=True):
        now = fields.Datetime.now()
        for issue in self:
            updates = {}
            if issue.state != 'todo' and not issue.start_date and 'start_date' not in keep:
                updates['start_date'] = min(now, issue.end_date) if issue.end_date else now
            if issue.state == 'done' and not issue.end_date:
                updates['end_date'] = now
            elif issue.state != 'done' and issue.end_date and clear and 'end_date' not in keep:
                updates['end_date'] = False
            if issue.state != 'in_progress' and issue.is_paused:
                updates['is_paused'] = False
            if updates:
                # No 'state' key, so this does not loop back into the sync.
                issue.write(updates)

    def _assign_keys(self):
        """Give each issue a key from its project (WEB-1, WEB-2...).

        An issue that moves to another project gets a key from the new one.
        """
        for issue in self.sorted('id'):
            project = issue.project
            if not project or not project.key:
                continue
            if issue.key and issue.key.startswith(project.key + '-'):
                continue
            number = project._next_issue_number()
            super(ManageTask, issue).write({'key': f"{project.key}-{number}"})

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_toggle_pause(self):
        if self.filtered(lambda t: t.state != 'in_progress' and not t.is_paused):
            raise UserError(_("Only issues in progress can be paused."))
        return super().action_toggle_pause()

    def action_open_complete_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Complete Issue") if len(self) == 1 else _("Complete Issues"),
            'res_model': 'manage.task.complete',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_ids': self.ids},
        }

    def action_assign_to_me(self):
        partner = self.env.user.partner_id
        if not partner.is_dev:
            raise RedirectWarning(
                _("Your contact is not marked as a developer yet. Turn on \"Developer\" "
                  "and enter an access code in your profile, then try again."),
                self.env.ref('manage_plus.action_my_developer_profile').id,
                _("Open My Developer Profile"))
        self.write({'assignee': partner.id})


class ManageTaskComplete(models.TransientModel):
    """Finish issues and take them off the board: archive (keep) or delete."""
    _name = 'manage.task.complete'
    _description = 'Complete Issues'

    task_ids = fields.Many2many(
        'manage.task', string="Issues", required=True,
        default=lambda self: self._default_tasks())
    mode = fields.Selection(
        [('archive', 'Archive (keep it for reference)'), ('delete', 'Delete permanently')],
        string="Then", required=True, default='archive')

    def _default_tasks(self):
        ctx = self.env.context
        if ctx.get('default_task_ids'):
            return ctx['default_task_ids']
        if ctx.get('active_model') == 'manage.task':
            return ctx.get('active_ids', [])
        return []

    def action_confirm(self):
        self.ensure_one()
        issues = self.task_ids.exists()
        issues.filtered(lambda i: i.state != 'done').action_done()
        if self.mode == 'archive':
            issues.write({'active': False})
        else:
            issues.unlink()
        # Back to the board: the issue is gone from it (and may not exist anymore).
        return self.env['ir.actions.act_window']._for_xml_id('manage.action_task_window')
