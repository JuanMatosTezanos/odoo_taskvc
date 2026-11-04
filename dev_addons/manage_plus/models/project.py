# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

KEY_RE = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')


class ManageProject(models.Model):
    _name = 'manage.project'
    _inherit = ['manage.project', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    key = fields.Char(
        tracking=True, copy=False,
        help="Short uppercase code used in issue keys, e.g. WEB gives WEB-1, WEB-2...")
    issue_sequence = fields.Integer(
        string="Last Issue Number", default=0, copy=False, readonly=True)
    active = fields.Boolean(default=True)
    manager_id = fields.Many2one(
        'res.users', string="Project Manager", default=lambda self: self.env.user, tracking=True)

    tasks = fields.One2many('manage.task', 'project', string="Issues")
    bug_count = fields.Integer(compute='_compute_counts')
    open_bug_count = fields.Integer(compute='_compute_counts')
    running_sprint = fields.Many2one('manage.sprint', compute='_compute_running_sprint')

    _sql_constraints = [
        ('key_unique', 'unique(key)', "Another project already uses this key."),
    ]

    # Replaces the base method: sprints no longer need active_test=False, and
    # issues are counted directly (they no longer need a history). The issue
    # count is open issues only, so finished work no longer inflates it.
    @api.depends('histories', 'sprints', 'tasks.issue_type', 'tasks.state', 'tasks.active')
    def _compute_counts(self):
        for project in self:
            bugs = project.tasks.filtered(lambda i: i.issue_type == 'bug')
            project.history_count = len(project.histories)
            project.sprint_count = len(project.sprints)
            project.task_count = len(project.tasks.filtered(lambda i: i.state != 'done'))
            project.bug_count = len(bugs)
            project.open_bug_count = len(bugs.filtered(lambda b: b.state != 'done'))

    @api.depends('sprints.state')
    def _compute_running_sprint(self):
        for project in self:
            project.running_sprint = project._get_running_sprint()

    def _get_running_sprint(self):
        """The running sprint of this project (empty if none, or no project)."""
        if len(self) != 1:
            return self.env['manage.sprint']
        return self.sprints.filtered(lambda s: s.state == 'running')[:1]

    # ------------------------------------------------------------------
    # Keys
    # ------------------------------------------------------------------

    @api.model
    def _suggest_key(self, name):
        """WEB for "Web", CP for "Customer Portal", plus a number if taken."""
        words = re.findall(r'[A-Za-z0-9]+', name or '')
        if len(words) > 1:
            base = ''.join(w[0] for w in words)[:4]
        else:
            base = (words[0] if words else 'PRJ')[:4]
        base = base.upper()
        if not base[0].isalpha():
            base = 'P' + base[:3]
        if len(base) < 2:
            base = (base + 'PRJ')[:3]
        key, n = base, 1
        while self.with_context(active_test=False).search_count([('key', '=', key)]):
            n += 1
            key = f"{base}{n}"
        return key

    @api.constrains('key')
    def _check_key(self):
        for project in self:
            if project.key and not KEY_RE.match(project.key):
                raise ValidationError(_(
                    "Project key %s is invalid: use 2-10 uppercase letters or digits, "
                    "starting with a letter (e.g. WEB).", project.key))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('key'):
                vals['key'] = vals['key'].strip().upper()
            else:
                vals['key'] = self._suggest_key(vals.get('name'))
        return super().create(vals_list)

    def write(self, vals):
        if 'key' in vals:
            vals = dict(vals, key=(vals['key'] or '').strip().upper() or False)
            if not vals['key']:
                raise UserError(_("A project needs a key."))
            # Changing it would leave old keys behind (and break links to them).
            if self.filtered(lambda p: p.key != vals['key'] and p.issue_sequence):
                raise UserError(_("The key cannot change once the project has issues."))
        return super().write(vals)

    def _next_issue_number(self):
        """Reserve the next issue number; one SQL update so two users never get the same."""
        self.ensure_one()
        self.flush_recordset(['issue_sequence'])
        self.env.cr.execute(
            "UPDATE manage_project SET issue_sequence = COALESCE(issue_sequence, 0) + 1 "
            "WHERE id = %s RETURNING issue_sequence", [self.id])
        number = self.env.cr.fetchone()[0]
        self.invalidate_recordset(['issue_sequence'])
        return number

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_sprints(self):
        return self._open_related('manage.sprint', _('Sprints'), view_mode='tree,calendar,form')

    def action_view_tasks(self):
        return self._open_related('manage.task', _('Issues'), view_mode='kanban,tree,form',
                                  context={'search_default_open': 1})

    def action_view_bugs(self):
        return self._open_related(
            'manage.task', _('Bugs'), view_mode='kanban,tree,form',
            context={'default_issue_type': 'bug', 'search_default_type_bug': 1,
                     'search_default_open': 1})

    def action_view_backlog(self):
        action = self.env['ir.actions.act_window']._for_xml_id('manage_plus.action_backlog')
        action['domain'] = [('project', '=', self.id), ('state', '!=', 'done'),
                            '|', ('sprint', '=', False), ('sprint.state', '!=', 'closed')]
        action['context'] = {'default_project': self.id, 'group_by': 'sprint'}
        return action
