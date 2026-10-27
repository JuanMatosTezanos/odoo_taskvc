from odoo import models, fields, api


class task(models.Model):
    _name = 'manage.task'
    _description = 'manage.task'

    name = fields.Char(string="Nombre", readonly=False, required=True, help="Introduzca el nombre") #Name
    description= fields.Text()
    creation_date = fields.Date()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()



