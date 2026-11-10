# -*- coding: utf-8 -*-
import re

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# 8 digits followed by letters, e.g. 12345678A.
ACCESS_CODE_RE = re.compile(r'^[0-9]{8}[A-Z]+$')


class ResPartner(models.Model):
    """Developer profile on a contact.

    Issues are assigned to Odoo users (like the Project app); the developer
    details (access code, technologies) live on that user's contact.
    Fields are prefixed with dev_ so they never clash with other modules.
    """
    _inherit = 'res.partner'

    dev_is_developer = fields.Boolean(string="Developer")
    dev_access_code = fields.Char(string="Access Code", copy=False)
    dev_access_code_locked = fields.Boolean(
        compute='_compute_dev_access_code_locked',
        help="True once an access code has been saved; it cannot change after that.")
    dev_technology_ids = fields.Many2many(
        'dev.technology', relation='dev_partner_technology_rel', column1='partner_id',
        column2='technology_id', string="Technologies")
    dev_last_login = fields.Datetime(string="Last Login", compute='_compute_dev_user_stats')
    dev_issue_count = fields.Integer(string="Issues", compute='_compute_dev_user_stats')
    dev_open_issue_count = fields.Integer(string="Open Issues", compute='_compute_dev_user_stats')

    _sql_constraints = [
        ('dev_access_code_unique', 'unique(dev_access_code)', "This access code is already used."),
    ]

    # No @api.depends on purpose: the value reflects what is saved in the
    # database and does not change while the user is typing in the form.
    # (Locking on the typed value made the field read-only mid-typing, so the
    # code was never sent on save.)
    def _compute_dev_access_code_locked(self):
        for partner in self:
            partner.dev_access_code_locked = bool(partner._origin.dev_access_code)

    def _compute_dev_user_stats(self):
        Task = self.env['project.task']
        for partner in self:
            users = partner.user_ids
            partner.dev_last_login = max(users.mapped('login_date'), default=False) if users else False
            if users:
                domain = [('dev_assignee_id', 'in', users.ids), ('project_id.dev_is_software', '=', True)]
                partner.dev_issue_count = Task.search_count(domain)
                partner.dev_open_issue_count = Task.search_count(domain + [('dev_status', '!=', 'done')])
            else:
                partner.dev_issue_count = partner.dev_open_issue_count = 0

    @api.constrains('dev_is_developer', 'dev_access_code')
    def _check_dev_access_code(self):
        for partner in self.filtered('dev_is_developer'):
            if not partner.dev_access_code:
                raise ValidationError(_("Access code is required for developers."))
            if not ACCESS_CODE_RE.match(partner.dev_access_code):
                raise ValidationError(_(
                    "Access code is invalid: use 8 digits followed by letters (e.g. 12345678A)."))

    @api.model
    def _dev_normalize_code(self, code):
        # Upper case, so 12345678a and 12345678A count as the same code.
        return code.strip().upper() if isinstance(code, str) else code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('dev_access_code'):
                vals['dev_access_code'] = self._dev_normalize_code(vals['dev_access_code'])
        partners = super().create(vals_list)
        partners.filtered('dev_is_developer')._dev_add_category()
        return partners

    def write(self, vals):
        if vals.get('dev_access_code'):
            vals = dict(vals, dev_access_code=self._dev_normalize_code(vals['dev_access_code']))
            for partner in self:
                if partner.dev_access_code and partner.dev_access_code != vals['dev_access_code']:
                    raise ValidationError(_("Access code cannot be modified once assigned."))
        res = super().write(vals)
        if vals.get('dev_is_developer'):
            self.filtered('dev_is_developer')._dev_add_category()
        return res

    def _dev_category(self):
        # sudo: regular users may not be allowed to create partner tags.
        Category = self.env['res.partner.category'].sudo()
        return Category.search([('name', '=', 'Devs')], limit=1) or Category.create({'name': 'Devs'})

    def _dev_add_category(self):
        if not self:
            return
        category = self._dev_category()
        missing = self.filtered(lambda p: category not in p.category_id)
        if missing:
            missing.write({'category_id': [Command.link(category.id)]})

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_dev_view_issues(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Issues"),
            'res_model': 'project.task',
            'view_mode': 'kanban,tree,form',
            'views': [(self.env.ref('dev_addons.task_kanban').id, 'kanban'),
                      (self.env.ref('dev_addons.task_list').id, 'list'),
                      (self.env.ref('project.view_task_form2').id, 'form')],
            'search_view_id': [self.env.ref('dev_addons.task_search').id],
            'domain': [('dev_assignee_id', 'in', self.user_ids.ids), ('project_id.dev_is_software', '=', True)],
            'context': {'default_dev_assignee_id': self.user_ids[:1].id, 'dev_board': True},
        }

    def action_dev_create_user(self):
        """Give a developer a login so issues can be assigned to them.

        The user is linked to this contact, so the developer profile (access
        code, technologies) stays on it. Creating it from Settings > Users
        would make a second contact instead."""
        self.ensure_one()
        if self.user_ids:
            raise UserError(_("%s already has a user.", self.name))
        if not self.email:
            raise UserError(_("Fill in %s's email first: it is used as their login.", self.name))
        if self.env['res.users'].with_context(active_test=False).search_count([('login', '=', self.email)]):
            raise UserError(_("A user with the login %s already exists.", self.email))
        user = self.env['res.users'].create({
            'partner_id': self.id,
            'login': self.email,
            'groups_id': [Command.link(self.env.ref('base.group_user').id),
                          Command.link(self.env.ref('project.group_project_user').id)],
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("%(name)s can now be assigned issues. Their login is %(login)s; "
                             "set a password in Settings > Users if no invitation email arrives.",
                             name=self.name, login=user.login),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    @api.model
    def action_dev_my_profile(self):
        """Open the current user's own contact in the developer form."""
        return {
            'type': 'ir.actions.act_window',
            'name': _("My Developer Profile"),
            'res_model': 'res.partner',
            'res_id': self.env.user.partner_id.id,
            'view_mode': 'form',
            'views': [(self.env.ref('dev_addons.developer_form').id, 'form')],
            'target': 'current',
        }
