from odoo import models, fields, api


class task(models.Model):
    _name = 'manage.task'
    _description = 'manage.task'

    code = fields.Char(compute="_get_code")
    name = fields.Char(string="Nombre", readonly=False, required=True, help="Introduzca el nombre") #Name
    description= fields.Text()
    creation_date = fields.Date()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()
    sprint = fields.Many2one("manage.sprint", ondelete="set null", help="sprint relacionado ")

    technology = fields.Many2many(comodel_name="manage.technology", relation="technologies_tasks", column1="task_id", column2 = "technology_id")


    def _get_code(self):
        for task in self:
            if len(task.sprint) == 0:
                task.code = "TSK_"+str(task.id)
            else:
                task.code = str(task.sprint.name).upper() + "_"+str(task.id)



class sprint(models.Model):
    _name = 'manage.sprint'
    _description = 'manage.sprint'

    name = fields.Char()
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime()

    task = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="sprint")


class technology(models.Model):
    _name = 'manage.technology'
    _description = 'manage.technology'

    name = fields.Char()
    description = fields.Text()

    photo = fields.Image(max_width=200, max_height=200)

    task = fields.Many2many (comodel_name="manage.task", relation = "technologies_tasks", column1="technology_id", column2="task_id")
    
