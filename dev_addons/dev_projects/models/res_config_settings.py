# -*- coding: utf-8 -*-
from odoo import fields, models

PARAM_IMAGE_DIR = 'dev_projects.tech_image_dir'
PARAM_SPRINT_DAYS = 'dev_projects.sprint_duration'
PARAM_DEFAULT_COLUMNS = 'dev_projects.default_columns'


class ResConfigSettings(models.TransientModel):
    """A "Dev Projects" section on the Project settings page."""
    _inherit = 'res.config.settings'

    dev_tech_image_dir = fields.Char(
        string="Technology Logo Folder", config_parameter=PARAM_IMAGE_DIR, default='/tech_images')
    dev_sprint_duration = fields.Integer(
        string="Default Sprint Length (days)", config_parameter=PARAM_SPRINT_DAYS, default=14)
    # Stored as 'yes'/'no' by hand: a Boolean with config_parameter deletes the
    # parameter when unticked, which would read back as the default (on).
    dev_default_columns = fields.Boolean(string="Default Board Columns for New Software Projects")

    def get_values(self):
        res = super().get_values()
        value = self.env['ir.config_parameter'].sudo().get_param(PARAM_DEFAULT_COLUMNS, 'yes')
        res['dev_default_columns'] = value != 'no'
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            PARAM_DEFAULT_COLUMNS, 'yes' if self.dev_default_columns else 'no')
