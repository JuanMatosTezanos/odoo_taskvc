# -*- coding: utf-8 -*-
import re

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

KEY_RE = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Software projects live in Dev Projects; the Project app hides them by
    # default (removable filter). Projects created from Dev Projects get it ticked.
    dev_is_software = fields.Boolean(
        string="Software Project", index=True, tracking=True,
        help="Managed in Dev Projects (board, backlog, sprints, issue keys). "
             "Hidden from the Project app's lists by default.")
    dev_key = fields.Char(
        string="Key", tracking=True, copy=False,
        help="Short uppercase code used in issue keys, e.g. WEB gives WEB-1, WEB-2...")
    dev_issue_sequence = fields.Integer(string="Last Issue Number", default=0, copy=False, readonly=True)

    dev_repository_url = fields.Char(
        string="GitHub Repository", tracking=True,
        help="Link to the project's code, e.g. https://github.com/company/project")

    dev_sprint_ids = fields.One2many('dev.sprint', 'project_id', string="Sprints")
    dev_running_sprint_id = fields.Many2one(
        'dev.sprint', string="Running Sprint", compute='_compute_dev_running_sprint')
    dev_open_issue_count = fields.Integer(string="Open Issues", compute='_compute_dev_counts')
    dev_open_bug_count = fields.Integer(string="Open Bugs", compute='_compute_dev_counts')
    dev_sprint_count = fields.Integer(string="Sprint Count", compute='_compute_dev_counts')

    _sql_constraints = [
        ('dev_key_unique', 'unique(dev_key)', "Another project already uses this key."),
    ]

    def _compute_dev_counts(self):
        Task = self.env['project.task']
        open_domain = [('project_id', 'in', self.ids), ('dev_status', '!=', 'done')]
        open_counts = dict(Task._read_group(open_domain, ['project_id'], ['__count']))
        bug_counts = dict(Task._read_group(open_domain + [('dev_issue_type', '=', 'bug')],
                                           ['project_id'], ['__count']))
        for project in self:
            project.dev_open_issue_count = open_counts.get(project, 0)
            project.dev_open_bug_count = bug_counts.get(project, 0)
            project.dev_sprint_count = len(project.dev_sprint_ids)

    @api.depends('dev_sprint_ids.state')
    def _compute_dev_running_sprint(self):
        for project in self:
            project.dev_running_sprint_id = project._dev_running_sprint()

    def _dev_running_sprint(self):
        """The running sprint of this project (empty if none, or no project)."""
        if len(self) != 1:
            return self.env['dev.sprint']
        return self.dev_sprint_ids.filtered(lambda s: s.state == 'running')[:1]

    # ------------------------------------------------------------------
    # Keys
    # ------------------------------------------------------------------

    @api.model
    def _dev_suggest_key(self, name):
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
        while self.with_context(active_test=False).sudo().search_count([('dev_key', '=', key)]):
            n += 1
            key = f"{base}{n}"
        return key

    @api.onchange('name', 'dev_is_software')
    def _onchange_name_dev_key(self):
        # Suggest a key for software projects; never change one in use.
        for project in self:
            if project.dev_is_software and project.name and not project.dev_issue_sequence \
                    and not project._origin.dev_key:
                project.dev_key = self._dev_suggest_key(project.name)

    @api.constrains('dev_key')
    def _check_dev_key(self):
        for project in self:
            if project.dev_key and not KEY_RE.match(project.dev_key):
                raise ValidationError(_(
                    "Project key %s is invalid: use 2-10 uppercase letters or digits, "
                    "starting with a letter (e.g. WEB).", project.dev_key))

    @api.model_create_multi
    def create(self, vals_list):
        default_stages = self.env['project.task.type']._dev_default_stages()
        if self.env['ir.config_parameter'].sudo().get_param('dev_projects.default_columns', 'yes') == 'no':
            default_stages = self.env['project.task.type']  # turned off in Settings
        default_software = self.env.context.get('default_dev_is_software')
        for vals in vals_list:
            if vals.get('dev_key'):
                vals['dev_key'] = vals['dev_key'].strip().upper()
            if not vals.get('dev_is_software', default_software):
                continue  # a regular project: plain Odoo behaviour
            if not vals.get('dev_key'):
                vals['dev_key'] = self._dev_suggest_key(vals.get('name'))
            if not vals.get('type_ids') and default_stages:
                # Give new software projects the default board columns.
                vals['type_ids'] = [Command.link(stage.id) for stage in default_stages]
            vals.update(self._dev_software_defaults())
        return super().create(vals_list)

    @api.model
    def _dev_software_defaults(self):
        # Software projects plan with milestones, and their tasks are "Issues"
        # (the "Name of the Tasks" field is hidden on them).
        return {'allow_milestones': True, 'label_tasks': 'Issues'}

    def write(self, vals):
        if 'dev_key' in vals:
            vals = dict(vals, dev_key=(vals['dev_key'] or '').strip().upper() or False)
            if not vals['dev_key'] and self.filtered('dev_is_software'):
                raise UserError(_("A software project needs a key."))
            # Changing it would leave old keys behind (and break links to them).
            if self.filtered(lambda p: p.dev_key != vals['dev_key'] and p.dev_issue_sequence):
                raise UserError(_("The key cannot change once the project has issues."))
        res = super().write(vals)
        if vals.get('dev_is_software'):
            self._dev_make_software()
        return res

    def _dev_make_software(self):
        """A project just became a software project: key, columns, milestones, numbered issues."""
        default_stages = self.env['project.task.type']._dev_default_stages()
        self.write(self._dev_software_defaults())
        for project in self:
            if not project.dev_key:
                project.dev_key = self._dev_suggest_key(project.name)
            if not project.type_ids and default_stages:
                project.type_ids = [Command.link(stage.id) for stage in default_stages]
            self.env['project.task'].with_context(active_test=False).search(
                [('project_id', '=', project.id), ('dev_key', '=', False)], order='id')._dev_assign_keys()

    def _dev_next_issue_number(self):
        """Reserve the next issue number; one SQL update so two users never get the same."""
        self.ensure_one()
        self.flush_recordset(['dev_issue_sequence'])
        self.env.cr.execute(
            "UPDATE project_project SET dev_issue_sequence = COALESCE(dev_issue_sequence, 0) + 1 "
            "WHERE id = %s RETURNING dev_issue_sequence", [self.id])
        number = self.env.cr.fetchone()[0]
        self.invalidate_recordset(['dev_issue_sequence'])
        return number

    # ------------------------------------------------------------------
    # Actions (open Dev Projects screens for this project)
    # ------------------------------------------------------------------

    def _dev_action(self, xmlid, extra_domain=None, extra_context=None):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(xmlid)
        action['domain'] = [('project_id', '=', self.id)] + (extra_domain or [])
        context = {'default_project_id': self.id, 'dev_board': True}
        context.update(extra_context or {})
        action['context'] = context
        action['display_name'] = f"{self.name} - {action['name']}"
        return action

    def action_dev_board(self):
        return self._dev_action('dev_projects.action_board',
                                extra_context={'search_default_dev_current_work': 1})

    def action_dev_open_issues(self):
        return self._dev_action('dev_projects.action_board',
                                extra_context={'search_default_dev_open': 1})

    def action_dev_bugs(self):
        return self._dev_action('dev_projects.action_board', extra_context={
            'default_dev_issue_type': 'bug', 'search_default_dev_type_bug': 1, 'search_default_dev_open': 1})

    def action_dev_backlog(self):
        action = self._dev_action('dev_projects.action_backlog')
        action['domain'] = [('project_id', '=', self.id), ('dev_status', '!=', 'done'),
                            '|', ('dev_sprint_id', '=', False), ('dev_sprint_id.state', '!=', 'closed')]
        action['context'].update(group_by='dev_sprint_id', dev_backlog=True)
        return action

    def action_dev_sprints(self):
        return self._dev_action('dev_projects.action_sprint')

    def action_dev_milestones(self):
        return self._dev_action('dev_projects.action_milestone')
