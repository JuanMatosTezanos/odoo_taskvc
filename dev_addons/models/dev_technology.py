# -*- coding: utf-8 -*-
import base64
import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

DEFAULT_IMAGE_DIR = '/tech_images'


class DevTechnology(models.Model):
    _name = 'dev.technology'
    _description = 'Technology'
    _order = 'name'

    name = fields.Char(required=True)
    description = fields.Text()
    color = fields.Integer()
    photo = fields.Image(max_width=200, max_height=200)

    task_ids = fields.Many2many(
        'project.task', relation='dev_task_technology_rel', column1='technology_id',
        column2='task_id', string="Issues")
    developer_ids = fields.Many2many(
        'res.partner', relation='dev_partner_technology_rel', column1='technology_id',
        column2='partner_id', string="Developers")
    task_count = fields.Integer(string="Issue Count", compute='_compute_counts')
    bug_count = fields.Integer(string="Bugs", compute='_compute_counts')
    developer_count = fields.Integer(string="Developer Count", compute='_compute_counts')

    _sql_constraints = [
        ('name_unique', 'unique(name)', "A technology with this name already exists."),
    ]

    @api.depends('task_ids.dev_issue_type', 'developer_ids')
    def _compute_counts(self):
        for tech in self:
            tech.task_count = len(tech.task_ids)
            tech.bug_count = len(tech.task_ids.filtered(lambda t: t.dev_issue_type == 'bug'))
            tech.developer_count = len(tech.developer_ids)

    @api.model
    def _find_photo(self, name):
        """Return the base64 logo for `name` from the image folder, or False.

        The match ignores case ("JS" finds JS.png), and os.path.basename stops
        names like "../x" from reading outside the folder.
        """
        if not name:
            return False
        folder = self.env['ir.config_parameter'].sudo().get_param(
            'dev_projects.tech_image_dir', DEFAULT_IMAGE_DIR)
        wanted = os.path.basename(name.strip()).lower() + '.png'
        try:
            match = next((f for f in os.listdir(folder) if f.lower() == wanted), None)
        except OSError:
            _logger.info("Technology image folder %s is not available", folder)
            return False
        if not match:
            return False
        with open(os.path.join(folder, match), 'rb') as image:
            return base64.b64encode(image.read())

    @api.onchange('name')
    def _onchange_name_photo(self):
        # Fill the logo from the folder, but never wipe one uploaded by hand.
        for tech in self:
            photo = self._find_photo(tech.name)
            if photo:
                tech.photo = photo

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('photo') and vals.get('name'):
                vals['photo'] = self._find_photo(vals['name'])
        return super().create(vals_list)
