# -*- coding: utf-8 -*-
from odoo import Command, _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    task = fields.Many2many(string="Issues")
    assigned_issue_ids = fields.One2many('manage.task', 'assignee', string="Assigned Issues")
    open_item_count = fields.Integer(
        string="Open Issues", compute='_compute_open_item_count',
        help="Issues assigned to this developer that are not done.")

    access_code_locked = fields.Boolean(
        compute='_compute_access_code_locked',
        help="True once an access code has been saved; it cannot change after that.")

    # No @api.depends on purpose: the value then reflects what is saved in the
    # database and does not change while the user is typing in the form.
    def _compute_access_code_locked(self):
        for partner in self:
            # _origin is the saved record (empty for a new one), even inside the form.
            partner.access_code_locked = bool(partner._origin.access_level)

    @api.depends('assigned_issue_ids.state')
    def _compute_open_item_count(self):
        for dev in self:
            dev.open_item_count = len(dev.assigned_issue_ids.filtered(lambda i: i.state != 'done'))

    @api.model
    def action_open_my_developer_profile(self):
        """Open the current user's own contact in the developer form."""
        return {
            'type': 'ir.actions.act_window',
            'name': _("My Developer Profile"),
            'res_model': 'res.partner',
            'res_id': self.env.user.partner_id.id,
            'view_mode': 'form',
            'views': [(self.env.ref('manage.devs_partner_form').id, 'form')],
            'target': 'current',
        }

    def action_view_dev_tasks(self):
        action = super().action_view_dev_tasks()
        action['name'] = _("Issues")
        return action

    @api.model
    def _normalize_access_code(self, code):
        # Stored upper case so the unique constraint is not bypassed by case.
        return code.strip().upper() if isinstance(code, str) else code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('access_level'):
                vals['access_level'] = self._normalize_access_code(vals['access_level'])
        partners = super().create(vals_list)
        partners.filtered('is_dev')._add_developer_category()
        return partners

    def write(self, vals):
        if vals.get('access_level'):
            vals = dict(vals, access_level=self._normalize_access_code(vals['access_level']))
        res = super().write(vals)
        if vals.get('is_dev'):
            self.filtered('is_dev')._add_developer_category()
        return res

    def _check_is_dev(self):
        # The base module tagged developers from inside a constraint, which
        # writes data during validation. Defined here without @api.constrains,
        # this override turns that constraint off; tagging now happens in
        # create() and write().
        return True

    def _get_category(self):
        # sudo: regular users may not be allowed to create partner tags.
        Category = self.env['res.partner.category'].sudo()
        category = Category.search([('name', '=', 'Devs')], limit=1)
        return category or Category.create({'name': 'Devs'})

    def _add_developer_category(self):
        if not self:
            return
        category = self._get_category()
        missing = self.filtered(lambda p: category not in p.category_id)
        if missing:
            missing.write({'category_id': [Command.link(category.id)]})
