from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from odoo import _
import logging
import re
import base64
from os import path


_logger = logging.getLogger(__name__)


TASK_STATES = [
    ('todo', 'To Do'),
    ('in_progress', 'In Progress'),
    ('review', 'In Review'),
    ('done', 'Done'),
]

PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Important'),
    ('2', 'High'),
    ('3', 'Critical'),
]


class developer(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    last_login = fields.Date()
    is_dev = fields.Boolean()
    # Only developers need an access code; the form makes it required when is_dev is set.
    access_level = fields.Char(string="Access Code")

    technologies = fields.Many2many('manage.technology', relation='developer_technologies', column1='developer_id', column2='technology_id')

    task = fields.Many2many('manage.task', relation='developers_tasks', column1='developer_id', column2='task_id')

    bugs = fields.Many2many('manage.bug', relation='developers_bugs', column1='developer_id', column2='bug_id')

    improvements = fields.Many2many('manage.improvement', relation='developers_improvements', column1='developer_id', column2='improvement_id')

    dev_task_count = fields.Integer(compute="_compute_dev_counts")
    dev_bug_count = fields.Integer(compute="_compute_dev_counts")
    dev_improvement_count = fields.Integer(compute="_compute_dev_counts")

    @api.depends('task', 'bugs', 'improvements')
    def _compute_dev_counts(self):
        for dev in self:
            dev.dev_task_count = len(dev.task)
            dev.dev_bug_count = len(dev.bugs)
            dev.dev_improvement_count = len(dev.improvements)

    @api.constrains("access_level", "is_dev")
    def _check_code(self):
        regex = re.compile(r'^[0-9]{8}[a-z]+$', re.I)
        for dev in self.filtered('is_dev'):
            if not dev.access_level:
                raise ValidationError(_("Access code is required for developers."))
            if not regex.match(dev.access_level):
                raise ValidationError(_("Access code is invalid: use 8 digits followed by letters (e.g. 12345678A)."))

    _sql_constraints = [('access_level_unique', 'unique(access_level)', 'Access level must be unique')]

    def _get_category(self):
        category = self.env['res.partner.category'].search([('name', '=', 'Devs')], limit=1)
        if not category:
            category = self.env['res.partner.category'].create({'name': 'Devs'})
        return category

    @api.onchange('is_dev')
    def _onchange_is_dev(self):
        if self.is_dev:
            self.category_id = [(4, self._get_category().id)]

    @api.constrains("is_dev")
    def _check_is_dev(self):
        category = self._get_category()
        for dev in self:
            if dev.is_dev:
                dev.category_id = [(4, category.id)]

    def write(self, vals):
        if 'access_level' in vals:
            for dev in self:
                if dev.access_level and vals['access_level'] != dev.access_level:
                    raise ValidationError(_("Access code cannot be modified once assigned."))
        return super().write(vals)

    def _open_related(self, model, name, field):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'kanban,tree,form',
            'domain': [(field, 'in', self.ids)],
            'context': {'current_developer': self.id},
        }

    def action_view_dev_tasks(self):
        return self._open_related('manage.task', _('Tasks'), 'developer')

    def action_view_dev_bugs(self):
        return self._open_related('manage.bug', _('Bugs'), 'developer')

    def action_view_dev_improvements(self):
        return self._open_related('manage.improvement', _('Improvements'), 'developer')


class project(models.Model):
    _name = 'manage.project'
    _description = 'Project'

    name = fields.Char(required=True)
    description = fields.Text()
    color = fields.Integer()

    histories = fields.One2many(comodel_name="manage.history", inverse_name="project")
    sprints = fields.One2many(comodel_name="manage.sprint", inverse_name="project")

    history_count = fields.Integer(compute="_compute_counts")
    sprint_count = fields.Integer(compute="_compute_counts")
    task_count = fields.Integer(compute="_compute_counts")

    @api.depends('histories', 'sprints', 'histories.tasks')
    def _compute_counts(self):
        for project in self:
            project.history_count = len(project.histories)
            project.sprint_count = len(project.with_context(active_test=False).sprints)
            project.task_count = len(project.histories.tasks)

    def _open_related(self, model, name, view_mode='tree,form', context=None):
        self.ensure_one()
        ctx = {'default_project': self.id}
        ctx.update(context or {})
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': view_mode,
            'domain': [('project', '=', self.id)],
            'context': ctx,
        }

    def action_view_histories(self):
        return self._open_related('manage.history', _('Histories'))

    def action_view_sprints(self):
        return self._open_related('manage.sprint', _('Sprints'), context={'active_test': False})

    def action_view_tasks(self):
        return self._open_related('manage.task', _('Tasks'), view_mode='kanban,tree,form')


class history(models.Model):
    _name = 'manage.history'
    _description = 'History'

    name = fields.Char(required=True)
    description = fields.Text()

    project = fields.Many2one("manage.project", ondelete="set null")

    tasks = fields.One2many(string="Tasks", comodel_name="manage.task", inverse_name="history")
    task_count = fields.Integer(compute="_compute_task_count")

    used_technologies = fields.Many2many("manage.technology", compute="_get_used_technologies")

    @api.depends('tasks')
    def _compute_task_count(self):
        for history in self:
            history.task_count = len(history.tasks)

    @api.depends('tasks.technology')
    def _get_used_technologies(self):
        for history in self:
            history.used_technologies = history.tasks.technology


class task(models.Model):
    _name = 'manage.task'
    _description = 'Task'
    _order = 'priority desc, id desc'

    def _get_definition_date(self):
        return datetime.datetime.now()

    definition_date = fields.Datetime(default=_get_definition_date)
    # Stored so lists can be grouped and filtered by project.
    project = fields.Many2one("manage.project", related="history.project", store=True, readonly=True)
    code = fields.Char(compute="_get_code")
    name = fields.Char(string="Name", readonly=False, required=True, help="Enter the name")
    history = fields.Many2one("manage.history", ondelete="set null", help="Related history")
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()
    state = fields.Selection(TASK_STATES, string="Status", default='todo', required=True, group_expand='_expand_states')
    priority = fields.Selection(PRIORITIES, default='0')
    color = fields.Integer()

    sprint = fields.Many2one("manage.sprint", compute="_get_sprint", store=True)

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_tasks", column1="task_id", column2="technology_id")

    def _expand_states(self, states, domain, order):
        # Always show every status column in the kanban, even empty ones.
        return [key for key, _label in TASK_STATES]

    def _get_code(self):
        for task in self:
            task.code = "TSK_" + str(task.id) if isinstance(task.id, int) else False

    @api.depends('history.project')
    def _get_sprint(self):
        now = datetime.datetime.now()
        for task in self:
            sprints = self.env['manage.sprint'].with_context(active_test=False).search(
                [('project', '=', task.history.project.id)]) if task.history.project else []
            current = False
            for sprint in sprints:
                if isinstance(sprint.end_date, datetime.datetime) and sprint.end_date > now:
                    current = sprint.id
            task.sprint = current

    def _get_default_dev(self):
        developer_id = self.env.context.get('current_developer')
        return [developer_id] if developer_id else []

    developer = fields.Many2many(comodel_name="res.partner", relation="developers_tasks", column1="task_id", column2="developer_id", domain=[('is_dev', '=', True)], default=_get_default_dev)

    def action_start(self):
        self.write({'state': 'in_progress', 'is_paused': False})
        for task in self.filtered(lambda t: not t.start_date):
            task.start_date = fields.Datetime.now()

    def action_review(self):
        self.write({'state': 'review'})

    def action_done(self):
        self.write({'state': 'done', 'is_paused': False, 'end_date': fields.Datetime.now()})

    def action_reset(self):
        self.write({'state': 'todo', 'end_date': False})

    def action_toggle_pause(self):
        for task in self:
            task.is_paused = not task.is_paused


class bug(models.Model):
    _name = 'manage.bug'
    _description = 'Bug'
    _inherit = 'manage.task'

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_bugs", column1="bug_id", column2="technology_id")

    task_linked = fields.Many2many(comodel_name="manage.task", relation="task_bugs", column1="bug_id", column2="task_id")

    bug_linked = fields.Many2many(comodel_name="manage.bug", relation="bugs_bugs", column1="bug1_id", column2="bug2_id")

    developer = fields.Many2many(comodel_name="res.partner", relation="developers_bugs", column1="bug_id", column2="developer_id", domain=[('is_dev', '=', True)])

    improvement_linked = fields.Many2many(comodel_name="manage.improvement", relation="improvements_bugs", column1="bug_id", column2="improvement_id")

    def _get_code(self):
        for bug in self:
            bug.code = "BUG_" + str(bug.id) if isinstance(bug.id, int) else False


class improvement(models.Model):
    _name = 'manage.improvement'
    _description = 'Improvement'
    _inherit = 'manage.task'

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_improvements", column1="improvement_id", column2="technology_id")

    history_linked = fields.Many2many("manage.history")

    developer = fields.Many2many(comodel_name="res.partner", relation="developers_improvements", column1="improvement_id", column2="developer_id", domain=[('is_dev', '=', True)])

    def _get_code(self):
        for improvement in self:
            improvement.code = "IMP_" + str(improvement.id) if isinstance(improvement.id, int) else False


class sprint(models.Model):
    _name = 'manage.sprint'
    _description = 'Sprint'
    _order = 'start_date desc'

    project = fields.Many2one("manage.project", ondelete="set null")
    duration = fields.Integer(default=15, help="Length of the sprint in days")
    name = fields.Char()
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime(compute="_get_end_date", store=True)

    tasks = fields.One2many(string="Tasks", comodel_name="manage.task", inverse_name="sprint")
    task_count = fields.Integer(compute="_compute_task_count")
    progress = fields.Float(compute="_compute_task_count", help="Percentage of finished tasks")
    # Note: Odoo treats a field named "active" as the archive flag, so finished
    # sprints are hidden by default. The menu action shows them anyway.
    active = fields.Boolean(compute="_get_active", store=True)

    @api.depends("start_date", "duration")
    def _get_end_date(self):
        for sprint in self:
            if isinstance(sprint.start_date, datetime.datetime) and sprint.duration > 0:
                sprint.end_date = sprint.start_date + datetime.timedelta(days=sprint.duration)
            else:
                sprint.end_date = sprint.start_date

    @api.depends('tasks', 'tasks.state')
    def _compute_task_count(self):
        for sprint in self:
            total = len(sprint.tasks)
            sprint.task_count = total
            done = len(sprint.tasks.filtered(lambda t: t.state == 'done'))
            sprint.progress = (done / total * 100.0) if total else 0.0

    @api.depends('start_date', 'duration')
    def _get_active(self):
        now = datetime.datetime.now()
        for sprint in self:
            sprint.active = bool(
                isinstance(sprint.start_date, datetime.datetime)
                and isinstance(sprint.end_date, datetime.datetime)
                and sprint.start_date <= now < sprint.end_date
            )

    @api.model
    def cron_update_sprints(self):
        sprints = self.with_context(active_test=False).search([])
        sprints._get_active()



class technology(models.Model):
    _name = 'manage.technology'
    _description = 'Technology'

    name = fields.Char()
    description = fields.Text()
    color = fields.Integer()

    photo = fields.Image(max_width=200, max_height=200)

    task = fields.Many2many(comodel_name="manage.task", relation="technologies_tasks", column1="technology_id", column2="task_id")
    developers = fields.Many2many('res.partner', relation='developer_technologies', column1='technology_id', column2='developer_id')
    task_count = fields.Integer(compute="_compute_counts")
    developer_count = fields.Integer(compute="_compute_counts")

    @api.depends('task', 'developers')
    def _compute_counts(self):
        for tech in self:
            tech.task_count = len(tech.task)
            tech.developer_count = len(tech.developers)

    @api.onchange('name')
    def _pic_change(self):
        for record in self:
            if not record.name:
                record.photo = False
                continue
            image_path = path.join("/tech_images", f"{record.name.lower().capitalize()}.png")
            if not path.exists(image_path):
                _logger.info("No image found for technology: %s", record.name)
                record.photo = False
                continue
            with open(image_path, "rb") as image:
                record.photo = base64.b64encode(image.read()).decode("utf-8")
