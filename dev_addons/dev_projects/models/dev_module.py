# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class DevModule(models.Model):
    """A part of the software (e.g. Login, Payments, Camera) used to classify
    issues, like a component in Jira. Each project has its own components."""
    _name = 'dev.module'
    _description = 'Component'
    _inherit = ['mail.thread']
    _order = 'project_id, sequence, name'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one('project.project', string="Project", required=True,
                                 domain=[('dev_is_software', '=', True)],
                                 index=True, ondelete='cascade', tracking=True,
                                 default=lambda self: self.env.context.get('default_project_id'))
    lead_id = fields.Many2one('res.users', string="Lead", tracking=True,
                              domain="[('share', '=', False), ('active', '=', True)]",
                              help="The person who knows this part of the software best.")
    description = fields.Text()
    color = fields.Integer()
    active = fields.Boolean(default=True)

    # Sub-tasks count inside their parent, not on their own.
    task_ids = fields.One2many('project.task', 'dev_module_id', string="Issues",
                               domain=[('display_in_project', '=', True)])
    issue_count = fields.Integer(string="Issue Count", compute='_compute_counts')
    open_count = fields.Integer(string="Open Issues", compute='_compute_counts')
    bug_count = fields.Integer(string="Open Bugs", compute='_compute_counts')
    technology_ids = fields.Many2many(
        'dev.technology', string="Technologies", compute='_compute_counts',
        help="Technologies used by the issues of this component.")

    _sql_constraints = [
        ('name_project_unique', 'unique(project_id, name)', "This project already has a component with that name."),
    ]

    @api.depends('task_ids.dev_status', 'task_ids.dev_issue_type', 'task_ids.dev_technology_ids')
    def _compute_counts(self):
        for module in self:
            issues = module.task_ids
            open_issues = issues.filtered(lambda i: i.dev_status != 'done')
            module.issue_count = len(issues)
            module.open_count = len(open_issues)
            module.bug_count = len(open_issues.filtered(lambda i: i.dev_issue_type == 'bug'))
            module.technology_ids = issues.dev_technology_ids

    def action_view_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dev_projects.action_board')
        action.update({
            'domain': [('dev_module_id', '=', self.id), ('display_in_project', '=', True)],
            'context': {'default_project_id': self.project_id.id, 'default_dev_module_id': self.id,
                        'dev_board': True},
            'display_name': _("%(project)s - %(module)s", project=self.project_id.name, module=self.name),
        })
        return action
