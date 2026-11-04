# -*- coding: utf-8 -*-
import base64
import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

DEFAULT_IMAGE_DIR = '/tech_images'


class ManageTechnology(models.Model):
    _inherit = 'manage.technology'

    name = fields.Char(required=True)

    task = fields.Many2many(string="Issues")
    bug_count = fields.Integer(compute='_compute_bug_count')

    _sql_constraints = [
        ('name_unique', 'unique(name)', "A technology with this name already exists."),
    ]

    @api.depends('task.issue_type')
    def _compute_bug_count(self):
        for tech in self:
            tech.bug_count = len(tech.task.filtered(lambda i: i.issue_type == 'bug'))

    @api.model
    def _find_photo(self, name):
        """Return the base64 logo for `name` from the image folder, or False.

        The base module looked for name.lower().capitalize() only, so "JS"
        searched for "Js.png" and missed "JS.png". The match is now
        case-insensitive, and os.path.basename stops names like "../x" from
        reading outside the folder.
        """
        if not name:
            return False
        folder = self.env['ir.config_parameter'].sudo().get_param(
            'manage_plus.tech_image_dir', DEFAULT_IMAGE_DIR)
        wanted = os.path.basename(name.strip()).lower() + '.png'
        try:
            match = next((f for f in os.listdir(folder) if f.lower() == wanted), None)
        except OSError:
            _logger.info("Technology image folder %s is not available", folder)
            return False
        if not match:
            _logger.info("No image found for technology: %s", name)
            return False
        with open(os.path.join(folder, match), 'rb') as image:
            return base64.b64encode(image.read())

    # Replaces the base onchange. It no longer wipes a photo uploaded by hand
    # when no image file matches the new name.
    @api.onchange('name')
    def _pic_change(self):
        for record in self:
            photo = self._find_photo(record.name)
            if photo:
                record.photo = photo

    @api.model_create_multi
    def create(self, vals_list):
        # The onchange only runs in the form; this also covers imports and demo data.
        for vals in vals_list:
            if not vals.get('photo') and vals.get('name'):
                vals['photo'] = self._find_photo(vals['name'])
        return super().create(vals_list)
