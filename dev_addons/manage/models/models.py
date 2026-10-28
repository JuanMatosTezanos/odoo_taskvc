from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from odoo import _



class project(models.Model):
    _name = 'manage.project'
    _description = 'manage.project'

    name = fields.Char()
    description = fields.Text()

    history = fields.One2many(comodel_name="manage.history", inverse_name="project")

class history(models.Model):
    _name = 'manage.history'
    _description = 'manage.history'

    name = fields.Char()
    description = fields.Text()

    
    project = fields.Many2one("manage.project", ondelete="set null")

    tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="history")



class task(models.Model):
    _name = 'manage.task'
    _description = 'manage.task'

    code = fields.Char(compute="_get_code")
    name = fields.Char(string="Nombre", readonly=False, required=True, help="Introduzca el nombre") #Name
    history = fields.Many2one("manage.history", ondelete="set null", help="historia relacionada ")
    description= fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()
    sprint = fields.Many2one("manage.sprint", ondelete="set null", help="sprint relacionado ")

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_tasks", column1="task_id", column2 = "technology_id")


    def _get_code(self):
        for task in self:
            try:
                if len(task.sprint) == 0:
                    task.code = "TSK_"+str(task.id)
                else:
                    task.code = str(task.sprint.name).upper() + "_"+str(task.id)
            except:
                raise ValidationError(_("bad code generation"))





class sprint(models.Model):
    _name = 'manage.sprint'
    _description = 'manage.sprint'
    
    duration = fields.Integer()
    name = fields.Char()
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime(compute="_get_end_date", store=True)

    task = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="sprint")

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
    
