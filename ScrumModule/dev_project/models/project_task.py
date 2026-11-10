# -*- coding: utf-8 -*-
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.project.models.project_task import CLOSED_STATES

from .project_task_type import DEV_STATUSES

ISSUE_TYPES = [
    ('story', 'Story'),
    ('task', 'Task'),
    ('bug', 'Bug'),
    ('improvement', 'Improvement'),
]

DEV_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Important'),
    ('2', 'High'),
    ('3', 'Critical'),
]

SEVERITIES = [
    ('minor', 'Minor'),
    ('major', 'Major'),
    ('critical', 'Critical'),
    ('blocker', 'Blocker'),
]


class ProjectTask(models.Model):
    """A project task is an issue.

    Everything is stored on project.task, so the same issue shows in the
    Project app and in Dev Projects. The dev_ fields add what software teams
    need; they are kept in sync with Project's own fields:

    * board column (stage) <-> status category <-> Project's Done state
    * assignee <-> Project's assignees (user_ids)
    * Dev priority (4 levels) <-> Project's star priority
    """
    _inherit = 'project.task'
    _rec_names_search = ['name', 'dev_key']

    dev_issue_type = fields.Selection(
        ISSUE_TYPES, string="Type", required=True, default='task', tracking=True, index=True)
    dev_project_is_software = fields.Boolean(related='project_id.dev_is_software', string="In a Software Project")
    dev_key = fields.Char(string="Key", readonly=True, copy=False, index=True,
                          help="Project key and number, e.g. WEB-42.")
    dev_status = fields.Selection(
        DEV_STATUSES, string="Status", compute='_compute_dev_status', store=True, index=True)
    dev_priority = fields.Selection(DEV_PRIORITIES, string="Dev Priority", default='0', tracking=True)
    dev_story_points = fields.Integer(string="Story Points", help="Relative effort estimate.")
    dev_severity = fields.Selection(SEVERITIES, string="Severity", default='minor', tracking=True)
    dev_is_blocking = fields.Boolean(
        string="Blocking Bug", compute='_compute_dev_is_blocking', store=True,
        help="A Critical or Blocker bug: shown first on the Board.")
    dev_sprint_id = fields.Many2one(
        'dev.sprint', string="Sprint", index=True, tracking=True, ondelete='set null',
        domain="[('project_id', '=', project_id), ('state', '!=', 'closed')]")
    dev_module_id = fields.Many2one(
        'dev.module', string="Component", index=True, tracking=True, ondelete='set null',
        domain="[('project_id', '=', project_id)]",
        help="The part of the software this issue is about, e.g. Login or Payments.")
    dev_assignee_id = fields.Many2one(
        'res.users', string="Assignee", index=True, tracking=True,
        domain="[('share', '=', False), ('active', '=', True)]",
        help="The one person responsible. Also added to the task's assignees.")
    dev_reporter_id = fields.Many2one(
        'res.users', string="Reported by", default=lambda self: self.env.user, tracking=True)
    dev_technology_ids = fields.Many2many(
        'dev.technology', relation='dev_task_technology_rel', column1='task_id',
        column2='technology_id', string="Technologies")
    dev_start_date = fields.Datetime(string="Started On", copy=False)
    dev_end_date = fields.Datetime(string="Finished On", copy=False)
    dev_is_paused = fields.Boolean(string="Paused", copy=False)
    dev_is_overdue = fields.Boolean(
        string="Overdue", compute='_compute_dev_is_overdue', search='_search_dev_is_overdue')

    _sql_constraints = [
        ('dev_key_unique', 'unique(dev_key)', "Issue keys must be unique."),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends('stage_id.dev_category', 'state')
    def _compute_dev_status(self):
        for task in self:
            if task.state in CLOSED_STATES:
                task.dev_status = 'done'
            else:
                category = task.stage_id.dev_category or 'todo'
                # Done is driven by Project's state; a reopened task in a
                # Done column counts as in progress until it is moved.
                task.dev_status = 'in_progress' if category == 'done' else category

    @api.depends('dev_issue_type', 'dev_severity')
    def _compute_dev_is_blocking(self):
        for task in self:
            task.dev_is_blocking = task.dev_issue_type == 'bug' and task.dev_severity in ('critical', 'blocker')

    @api.depends('date_deadline', 'dev_status')
    def _compute_dev_is_overdue(self):
        now = fields.Datetime.now()
        for task in self:
            task.dev_is_overdue = bool(
                task.date_deadline and task.dev_status != 'done' and task.date_deadline < now)

    def _search_dev_is_overdue(self, operator, value):
        if operator not in ('=', '!='):
            raise UserError(_("Unsupported search on Overdue."))
        now = fields.Datetime.now()
        if (operator == '=') == bool(value):
            return [('date_deadline', '<', now), ('dev_status', '!=', 'done')]
        return ['|', '|', ('date_deadline', '=', False),
                ('date_deadline', '>=', now), ('dev_status', '=', 'done')]

    @api.depends('name', 'dev_key')
    def _compute_display_name(self):
        super()._compute_display_name()
        for task in self:
            if task.dev_key:
                task.display_name = f"[{task.dev_key}] {task.display_name}"

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stages = super()._read_group_stage_ids(stages, domain, order)
        if not self.env.context.get('dev_board'):
            return stages
        # Dev board: always show the columns, even empty ones.
        project_id = self.env.context.get('default_project_id')
        Stage = self.env['project.task.type']
        if project_id:
            extra = Stage.search([('project_ids', '=', project_id)])
        else:
            extra = Stage._dev_default_stages()
        return (stages | extra).sorted(lambda s: (s.sequence, s.id))

    @api.model
    def _dev_on_board(self):
        """Opened from the Board (not the Backlog, which plans issues into sprints by hand)."""
        ctx = self.env.context
        return bool(ctx.get('dev_board') and not ctx.get('dev_backlog'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parent = self.browse(res.get('parent_id') or [])
        if parent and res.get('display_in_project') is False:
            # New sub-task (parent's Sub-tasks tab): same sprint and component as its parent.
            if 'dev_sprint_id' in fields_list:
                res['dev_sprint_id'] = parent.dev_sprint_id.id or False
            if 'dev_module_id' in fields_list and not res.get('dev_module_id'):
                res['dev_module_id'] = parent.dev_module_id.id or False
        elif 'dev_sprint_id' in fields_list and not res.get('dev_sprint_id') \
                and res.get('project_id') and self._dev_on_board():
            # New issue on the board: the running sprint, shown in the form.
            running = self.env['project.project'].browse(res['project_id'])._dev_running_sprint()
            if running:
                res['dev_sprint_id'] = running.id
        if 'milestone_id' in fields_list and not res.get('milestone_id') and res.get('dev_sprint_id'):
            # A sprint working towards a milestone: the issue is part of it too.
            res['milestone_id'] = self.env['dev.sprint'].browse(res['dev_sprint_id']).milestone_id.id or False
        return res

    @api.onchange('project_id')
    def _onchange_project_id_dev(self):
        for task in self:
            if task.dev_sprint_id.project_id != task.project_id:
                task.dev_sprint_id = False
            if task.dev_module_id.project_id != task.project_id:
                task.dev_module_id = False
            if not task._origin and not task.dev_sprint_id and task.project_id and self._dev_on_board() \
                    and task.display_in_project:  # sub-tasks take their parent's sprint
                # Project picked in a new board issue: its running sprint.
                task.dev_sprint_id = task.project_id._dev_running_sprint()

    @api.onchange('dev_sprint_id')
    def _onchange_dev_sprint_id_milestone(self):
        for task in self:
            if task.dev_sprint_id.milestone_id and not task.milestone_id:
                task.milestone_id = task.dev_sprint_id.milestone_id

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('project_id', 'milestone_id', 'dev_sprint_id', 'dev_module_id')
    def _check_dev_project_consistency(self):
        for task in self:
            records = [(task.dev_sprint_id, _("sprint")), (task.dev_module_id, _("component"))]
            if task.project_id.dev_is_software:
                # Regular projects keep Odoo's own (looser) milestone rules.
                records.append((task.milestone_id, _("milestone")))
            for record, label in records:
                if record and record.project_id != task.project_id:
                    if not task.project_id:
                        raise ValidationError(_(
                            "%(issue)s: set a project before choosing %(what)s %(name)s.",
                            issue=task.display_name, what=label, name=record.name))
                    raise ValidationError(_(
                        "%(issue)s: %(what)s %(name)s belongs to project %(other)s, not %(project)s.",
                        issue=task.display_name, what=label, name=record.name,
                        other=record.project_id.name, project=task.project_id.name))

    @api.constrains('dev_start_date', 'dev_end_date')
    def _check_dev_dates(self):
        for task in self:
            if task.dev_start_date and task.dev_end_date and task.dev_end_date < task.dev_start_date:
                raise ValidationError(_("%s: the end date cannot be before the start date.",
                                        task.display_name))

    def _dev_check_wip_limits(self):
        """Refuse to put more issues in a column than its WIP limit allows (per project and sprint).
        Done columns have no limit: finished work is not work in progress.
        Sub-tasks are not cards on the board (they live in their parent), so they don't count."""
        groups = {(t.stage_id, t.project_id, t.dev_sprint_id) for t in self
                  if t.display_in_project and t.stage_id.dev_wip_limit and t.stage_id.dev_category != 'done'}
        for stage, project, sprint in groups:
            count = self.search_count([
                ('stage_id', '=', stage.id), ('project_id', '=', project.id),
                ('dev_sprint_id', '=', sprint.id), ('display_in_project', '=', True),
            ])
            if count > stage.dev_wip_limit:
                raise UserError(_(
                    "Column %(stage)s allows %(limit)s issues and would have %(count)s. "
                    "Finish something first or raise the WIP limit.",
                    stage=stage.name, limit=stage.dev_wip_limit, count=count))

    # ------------------------------------------------------------------
    # Create / write: keep Dev fields and Project fields in sync
    # ------------------------------------------------------------------

    @api.model
    def _dev_priority_to_star(self, dev_priority):
        return '1' if dev_priority in ('2', '3') else '0'

    def _dev_software(self):
        """The tasks of software projects. Dev behaviour (column/Done sync,
        assignee and priority sync, keys, WIP limits) only applies to these, so
        other teams' projects behave exactly like the plain Project app."""
        return self.filtered(lambda t: t.project_id.dev_is_software)

    def _dev_prepare_vals(self, vals):
        """Changes that can be decided from `vals` alone. Only the Dev screens
        set these fields, so they are safe for every task."""
        if vals.get('dev_assignee_id'):
            vals['user_ids'] = list(vals.get('user_ids', [])) + [Command.link(vals['dev_assignee_id'])]
        if 'dev_priority' in vals and 'priority' not in vals:
            vals['priority'] = self._dev_priority_to_star(vals['dev_priority'])
        return vals

    def _dev_mark_done_in_done_columns(self):
        # A Done column marks the task done in Project too.
        to_close = self.filtered(lambda t: t.stage_id.dev_category == 'done' and t.state not in CLOSED_STATES)
        if to_close:
            super(ProjectTask, to_close).write({'state': '1_done'})

    @api.model_create_multi
    def create(self, vals_list):
        Project = self.env['project.project']
        dev_context = self.env.context.get('dev_board')
        on_board = self._dev_on_board()
        to_backlog = []  # board issues that found no running sprint
        for vals in vals_list:
            # Sub-tasks get their sprint from their parent (see _dev_follow_parent).
            subtask = vals.get('parent_id') and (not vals.get('project_id') or vals.get('display_in_project') is False)
            if dev_context and not subtask and not vals.get('project_id') \
                    and not self.env.context.get('default_project_id'):
                # Dev Projects and only one software project: use it.
                projects = Project.search([('dev_is_software', '=', True)], limit=2)
                if len(projects) == 1:
                    vals['project_id'] = projects.id
            project = Project.browse(vals.get('project_id') or self.env.context.get('default_project_id') or [])
            if on_board and not subtask and project.dev_is_software and not vals.get('dev_sprint_id') \
                    and not self.env.context.get('default_dev_sprint_id'):
                # Created on the board: put it in the running sprint. The form
                # already shows it as the default (see default_get); this covers
                # quick create and code. An emptied Sprint field in the form is kept.
                running = project._dev_running_sprint()
                if 'dev_sprint_id' not in vals:
                    vals['dev_sprint_id'] = running.id
                if not running:
                    to_backlog.append(vals.get('name') or '')
            self._dev_prepare_vals(vals)
        tasks = super().create(vals_list)
        tasks._dev_follow_parent()
        tasks._dev_fill_milestone_from_sprint()
        software = tasks._dev_software()
        for task in software:
            if not task.dev_assignee_id and task.user_ids:
                # Created in the Project app: first assignee is the Dev assignee.
                task.sudo().dev_assignee_id = task.user_ids[:1]
        software._dev_mark_done_in_done_columns()
        software._dev_sync_stage_and_dates(clear=False)
        software._dev_assign_keys()
        software._dev_check_wip_limits()
        if to_backlog:
            self._dev_notify_backlog(to_backlog)
        return tasks

    def _dev_notify_backlog(self, names):
        """Tell the user why a new board issue is not in a sprint (so it never
        looks like it vanished): no sprint is running, so it went to the backlog."""
        if len(names) == 1:
            message = _("No sprint is running, so \"%s\" went to the backlog. "
                        "Start a sprint (Sprints > Start) to work on it on the Board.", names[0])
        else:
            message = _("No sprint is running, so %s issues went to the backlog. "
                        "Start a sprint (Sprints > Start) to work on them on the Board.", len(names))
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
            'title': _("Added to the backlog"),
            'message': message,
            'type': 'info',
            'sticky': False,
        })

    def _dev_fill_milestone_from_sprint(self):
        """Issues in a sprint that works towards a milestone belong to that
        milestone too (unless they already have one)."""
        for task in self.filtered(lambda t: not t.milestone_id and t.dev_sprint_id.milestone_id):
            super(ProjectTask, task.sudo()).write({'milestone_id': task.dev_sprint_id.milestone_id.id})

    # ------------------------------------------------------------------
    # Sub-tasks: listed inside their parent (Sub-tasks tab), not on the board
    # ------------------------------------------------------------------

    def _dev_subtasks(self):
        """Sub-tasks shown only inside their parent (Odoo's default for the
        Sub-tasks tab). They are not counted on their own in sprints, milestones
        and components: their parent is."""
        return self.with_context(active_test=False).child_ids.filtered(
            lambda t: not t.display_in_project and t.project_id == t.parent_id.project_id)

    def _dev_follow_parent(self):
        """Sub-tasks are in their parent's sprint, and take its component if they have none."""
        for task in self.filtered(lambda t: t.parent_id and not t.display_in_project
                                  and t.project_id == t.parent_id.project_id):
            parent = task.parent_id
            vals = {}
            if task.dev_sprint_id != parent.dev_sprint_id:
                vals['dev_sprint_id'] = parent.dev_sprint_id.id
            if not task.dev_module_id and parent.dev_module_id:
                vals['dev_module_id'] = parent.dev_module_id.id
            if vals:
                task.sudo().write(vals)

    def _dev_update_subtasks(self, vals, old_modules):
        """The parent's sprint or component changed: its sub-tasks follow. Sub-tasks
        given another component on purpose keep it."""
        for task in self:
            subtasks = task._dev_subtasks()
            if 'dev_sprint_id' in vals:
                moving = subtasks.filtered(lambda s: s.dev_sprint_id != task.dev_sprint_id)
                if moving:
                    moving.sudo().write({'dev_sprint_id': task.dev_sprint_id.id})
            if 'dev_module_id' in vals:
                old = old_modules.get(task.id)
                following = subtasks.filtered(
                    lambda s: s.dev_module_id != task.dev_module_id
                    and (not s.dev_module_id or s.dev_module_id == old))
                if following:
                    following.sudo().write({'dev_module_id': task.dev_module_id.id})

    def _dev_drop_other_project_links(self, vals):
        """Issues moving to another project leave their sprint and module behind
        (they belong to the old project), unless `vals` sets new ones. Odoo
        already does the same for the milestone."""
        new_project_id = vals.get('project_id') or False
        for fname in ('dev_sprint_id', 'dev_module_id'):
            if fname in vals:
                continue
            stale = self.filtered(lambda t: t[fname] and t[fname].project_id.id != new_project_id)
            if stale:
                super(ProjectTask, stale).write({fname: False})

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        default = default or {}
        # Duplicating a project copies its milestones and modules first: point to the copies.
        mappings = {'milestone_id': self.env.context.get('milestone_mapping') or {},
                    'dev_module_id': self.env.context.get('dev_module_mapping') or {}}
        for vals in vals_list:
            for fname, mapping in mappings.items():
                if vals.get(fname) and fname not in default:
                    vals[fname] = mapping.get(vals[fname], vals[fname])
            # Copied into another project: the old project's sprint, milestone
            # and module do not apply there.
            for fname in ('dev_sprint_id', 'milestone_id', 'dev_module_id'):
                if fname not in default and vals.get(fname):
                    record = self.env[self._fields[fname].comodel_name].browse(vals[fname])
                    if record.project_id.id != vals.get('project_id'):
                        vals[fname] = False
        return vals_list

    def write(self, vals):
        vals = self._dev_prepare_vals(dict(vals))
        if 'project_id' in vals:
            self._dev_drop_other_project_links(vals)
        reopen = self.env['project.task']
        if vals.get('stage_id') and 'state' not in vals:
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            if stage.dev_category != 'done':
                # Cards dragged out of a Done column reopen. Otherwise keep the
                # Project app's rule: a closed task stays closed when it changes stage.
                reopen = self._dev_software().filtered(
                    lambda t: t.state == '1_done' and t.stage_id.dev_category == 'done')
        old_modules = {t.id: t.dev_module_id for t in self} if 'dev_module_id' in vals else {}
        res = super().write(vals)
        if 'dev_sprint_id' in vals or 'dev_module_id' in vals:
            self._dev_update_subtasks(vals, old_modules)
        if {'parent_id', 'display_in_project'} & set(vals):
            self._dev_follow_parent()
        if vals.get('dev_sprint_id') and 'milestone_id' not in vals:
            self._dev_fill_milestone_from_sprint()
        software = self._dev_software()
        if reopen:
            reopen.write({'state': '01_in_progress'})
        if vals.get('stage_id') and 'state' not in vals:
            software._dev_mark_done_in_done_columns()
        if 'user_ids' in vals and 'dev_assignee_id' not in vals:
            # Assignees changed in the Project app: keep the Dev assignee one of them.
            for task in software.filtered(lambda t: t.dev_assignee_id not in t.user_ids):
                super(ProjectTask, task.sudo()).write({'dev_assignee_id': task.user_ids[:1].id})
        if 'priority' in vals and 'dev_priority' not in vals:
            for task in software:
                if task.priority == '1' and task.dev_priority in ('0', '1'):
                    super(ProjectTask, task.sudo()).write({'dev_priority': '2'})
                elif task.priority == '0' and task.dev_priority in ('2', '3'):
                    super(ProjectTask, task.sudo()).write({'dev_priority': '0'})
        if 'stage_id' in vals or 'state' in vals:
            software._dev_sync_stage_and_dates(keep=set(vals))
        if 'project_id' in vals:
            software._dev_assign_keys()
        if {'stage_id', 'project_id', 'dev_sprint_id'} & set(vals):
            software._dev_check_wip_limits()
        return res

    def _dev_sync_stage_and_dates(self, keep=(), clear=True):
        """After a stage or state change: matching column, start/end dates, pause.

        These follow-up writes (and the key/assignee/priority syncs) use sudo:
        they are bookkeeping, and portal users of a shared project may move
        cards but are not allowed to write the dev_ fields themselves."""
        Stage = self.env['project.task.type']
        now = fields.Datetime.now()
        for task in self:
            if task.project_id and 'stage_id' not in keep:
                # Marked done / reopened in the Project app: move the card to match.
                if task.state in CLOSED_STATES and task.stage_id.dev_category != 'done':
                    stage = Stage._dev_for_category('done', task.project_id)
                    if stage:
                        super(ProjectTask, task.sudo()).write({'stage_id': stage.id})
                elif task.state not in CLOSED_STATES and task.stage_id.dev_category == 'done':
                    stage = Stage._dev_for_category('in_progress', task.project_id)
                    if stage:
                        super(ProjectTask, task.sudo()).write({'stage_id': stage.id})
            updates = {}
            status = task.dev_status
            if status != 'todo' and not task.dev_start_date and 'dev_start_date' not in keep:
                updates['dev_start_date'] = min(now, task.dev_end_date) if task.dev_end_date else now
            if status == 'done' and not task.dev_end_date:
                updates['dev_end_date'] = now
            elif status != 'done' and task.dev_end_date and clear and 'dev_end_date' not in keep:
                updates['dev_end_date'] = False
            if status != 'in_progress' and task.dev_is_paused:
                updates['dev_is_paused'] = False
            if updates:
                super(ProjectTask, task.sudo()).write(updates)

    def _dev_assign_keys(self):
        """Give each issue a key from its project (WEB-1, WEB-2...); a new one if it changes project."""
        for task in self.sorted('id'):
            project = task.project_id
            if not project or not project.dev_key:
                continue
            if task.dev_key and task.dev_key.startswith(project.dev_key + '-'):
                continue
            number = project.sudo()._dev_next_issue_number()
            super(ProjectTask, task.sudo()).write({'dev_key': f"{project.dev_key}-{number}"})

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def _dev_move_to(self, category):
        Stage = self.env['project.task.type']
        for task in self:
            if not task.project_id:
                raise UserError(_("%s has no project, so it has no board columns.", task.display_name))
            stage = Stage._dev_for_category(category, task.project_id)
            if not stage:
                label = dict(DEV_STATUSES)[category]
                raise UserError(_(
                    "Project %(project)s has no '%(category)s' column. Add one under "
                    "Configuration > Board Columns.", project=task.project_id.name, category=label))
            task.stage_id = stage

    def action_dev_start(self):
        self._dev_move_to('in_progress')

    def action_dev_review(self):
        self._dev_move_to('review')

    def action_dev_done(self):
        self._dev_move_to('done')

    def action_dev_reopen(self):
        self.write({'state': '01_in_progress'})
        self._dev_move_to('todo')

    def action_dev_toggle_pause(self):
        if self.filtered(lambda t: t.dev_status != 'in_progress' and not t.dev_is_paused):
            raise UserError(_("Only issues in progress can be paused."))
        for task in self:
            task.dev_is_paused = not task.dev_is_paused

    def action_dev_assign_to_me(self):
        self.write({'dev_assignee_id': self.env.user.id})

    def action_dev_open_complete_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Complete Issue") if len(self) == 1 else _("Complete Issues"),
            'res_model': 'dev.task.complete',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_ids': self.ids},
        }


class DevTaskComplete(models.TransientModel):
    """Finish issues and take them off the board: archive (keep) or delete."""
    _name = 'dev.task.complete'
    _description = 'Complete Issues'

    task_ids = fields.Many2many(
        'project.task', string="Issues", required=True,
        default=lambda self: self._default_tasks())
    mode = fields.Selection(
        [('archive', 'Archive (keep it for reference)'), ('delete', 'Delete permanently')],
        string="Then", required=True, default='archive')

    def _default_tasks(self):
        ctx = self.env.context
        if ctx.get('default_task_ids'):
            return ctx['default_task_ids']
        if ctx.get('active_model') == 'project.task':
            return ctx.get('active_ids', [])
        return []

    def action_confirm(self):
        self.ensure_one()
        tasks = self.task_ids.exists()
        software = bool(tasks._dev_software())
        projects = tasks.project_id
        open_tasks = tasks.filtered(lambda t: t.dev_status != 'done')
        open_tasks.write({'state': '1_done'})
        if self.mode == 'archive':
            tasks.write({'active': False})
        else:
            tasks.unlink()
        # Back to a task screen: the issue is gone from it (and may not exist
        # anymore). The action is also in the Project app's Action menu, so
        # regular tasks go back to the Project app, not to Dev Projects.
        if software:
            return self.env['ir.actions.act_window']._for_xml_id('dev_addons.action_board')
        if len(projects) == 1:
            return projects.action_view_tasks()
        return self.env['ir.actions.act_window']._for_xml_id('project.action_view_all_task')
