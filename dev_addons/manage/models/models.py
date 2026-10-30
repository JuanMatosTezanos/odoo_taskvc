from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from odoo import _
import logging


_logger = logging.getLogger(__name__)

class developer(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_dev = fields.Boolean()


    technologies = fields.Many2many('manage.technology', relation='developer_technologies', column1='developer_id', column2='technology_id')

    @api.onchange('is_dev')
    def _onchange_is_dev(self):
        categories = self.env['res.partner.category'].search([('name', '=', 'Devs')])
        if len(categories) > 0:
            category = categories[0]
        else:
            category = self.env['res.partner.category'].create({'name': 'Devs'})
        self.category_id = [(4,category.id)]


class project(models.Model):
    _name = 'manage.project'
    _description = 'manage.project'

    name = fields.Char()
    description = fields.Text()

    histories = fields.One2many(comodel_name="manage.history", inverse_name="project")



class history(models.Model):
    _name = 'manage.history'
    _description = 'manage.history'

    name = fields.Char()
    description = fields.Text()

    
    project = fields.Many2one("manage.project", ondelete="set null")

    tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="history")

    used_technologies = fields.Many2many("manage.technology", compute="_get_used_technologies")

    def _get_used_technologies(self):
        for history in self:
            technologies = None
            for task in history.tasks:
                if not technologies:
                    technologies = task.technology
                else:
                    technologies = technologies + task.technology
            history.used_technologies = technologies


class task(models.Model):
    _name = 'manage.task'
    _description = 'manage.task'

    def _get_definition_date(self):
            return datetime.datetime.now()

    definition_date = fields.Datetime(default=_get_definition_date)
    project = fields.Many2one("manage.project", related="history.project", readonly=True)
    code = fields.Char(compute="_get_code")
    name = fields.Char(string="Nombre", readonly=False, required=True, help="Introduzca el nombre") #Name
    history = fields.Many2one("manage.history", ondelete="set null", help="historia relacionada ")
    description= fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()

    sprint = fields.Many2one("manage.sprint", compute="_get_sprint", store=True)

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_tasks", column1="task_id", column2 = "technology_id")

    developer = fields.Many2many("res.partner", domain=[('is_dev', '=', True)])

    def _get_code(self):
        for task in self:
            try:
                task.code = "TSK_"+str(task.id)
                _logger.info("fields code generated for task with id: "+task.code)
            except:
                raise ValidationError(_("bad code generation"))

    @api.depends('code')
    def _get_sprint(self):
        for task in self:
            sprints = self.env['manage.sprint'].search([('project.id', '=', task.history.project.id)])
            found = False
            for sprint in sprints:
                if isinstance(sprint.end_date,datetime.datetime) and sprint.end_date > datetime.datetime.now():
                    task.sprint = sprint.id
                    found = True
            if not found:
                task.sprint = False

class bug(models.Model):
    _name = 'manage.bug'
    _description = 'manage.bug'
    _inherit = 'manage.task'


    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_bugs", column1="bug_id", column2 = "technology_id")

    task_linked = fields.Many2many(comodel_name="manage.task", relation="task_bugs", column1="bug_id", column2 = "task_id")

    bug_linked = fields.Many2many(comodel_name="manage.bug", relation="bugs_bugs", column1="bug1_id", column2 = "bug2_id")

    developers = fields.Many2many(comodel_name="res.partner", relation="developers_bugs", column1="bug_id", column2 = "developer_id")

    improvement_linked = fields.Many2many(comodel_name="manage.improvement", relation="improvements_bugs", column1="bug_id", column2 = "improvement_id")



class improvement(models.Model):
    _name = 'manage.improvement'
    _description = 'manage.improvement'
    _inherit = 'manage.task'


    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_improvements", column1="improvement_id", column2 = "technology_id")

    history_linked = fields.Many2many("manage.history")

    developers = fields.Many2many(comodel_name="res.partner", relation="developers_improvements", column1="improvement_id", column2 = "developer_id")





class sprint(models.Model):
    _name = 'manage.sprint'
    _description = 'manage.sprint'

    project = fields.Many2one("manage.project",ondelete="set null")
    duration = fields.Integer(default=15)
    name = fields.Char()
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime(compute="_get_end_date")

    tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="sprint")

    @api.depends("start_date", "end_date")
    def _get_end_date(self):
        for sprint in self:
            if isinstance(sprint.start_date, datetime.datetime) and sprint.duration > 0:
                sprint.end_date = sprint.start_date + datetime.timedelta(days=sprint.duration)
            else:
                sprint.end_date = sprint.start_date


class technology(models.Model):
    _name = 'manage.technology'
    _description = 'manage.technology'

    name = fields.Char()
    description = fields.Text()

    photo = fields.Image(max_width=200, max_height=200)

    task = fields.Many2many (comodel_name="manage.task", relation = "technologies_tasks", column1="technology_id", column2="task_id")
    

