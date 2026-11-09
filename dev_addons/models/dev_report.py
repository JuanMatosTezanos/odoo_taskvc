# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

REPORT_KINDS = [
    ('bug', "Something's broken"),
    ('feature', "Request a feature"),
    ('question', "Question"),
]

URGENCIES = [
    ('low', "It can wait"),
    ('normal', "Normal"),
    ('high', "Urgent"),
    ('blocking', "I can't work"),
]

# What the reporter sees, in order.
PROGRESS = [
    ('new', "Waiting for review"),
    ('accepted', "Accepted"),
    ('in_progress', "Being worked on"),
    ('done', "Done"),
    ('declined', "Declined"),
]

# How a report becomes an issue.
KIND_TO_TYPE = {'bug': 'bug', 'feature': 'story', 'question': 'task'}
URGENCY_TO_PRIORITY = {'low': '0', 'normal': '0', 'high': '2', 'blocking': '3'}
URGENCY_TO_SEVERITY = {'low': 'minor', 'normal': 'minor', 'high': 'major', 'blocking': 'blocker'}

# Only the dev team decides what happens to a report.
TRIAGE_FIELDS = {'state', 'task_id', 'decline_reason', 'project_id'}


class DevReport(models.Model):
    """Something a non-developer sends to the dev team: a problem, a wish or
    a question. The team accepts it (it becomes an issue in the Backlog) or
    declines it with a reason. The reporter follows it in "My Reports"."""
    _name = 'dev.report'
    _description = 'Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string="Title", required=True, tracking=True,
                       help="In a few words, e.g. \"Can't print invoices\".")
    app_menu_id = fields.Many2one(
        'ir.ui.menu', string="App", tracking=True, ondelete='set null',
        domain="[('id', 'in', allowed_app_ids)]",
        help="The Odoo app where it happens, e.g. Sales or Inventory.")
    allowed_app_ids = fields.Many2many('ir.ui.menu', compute='_compute_allowed_app_ids')
    # Chosen by the team when accepting: reporters don't see projects.
    project_id = fields.Many2one(
        'project.project', string="Project", readonly=True, tracking=True, index=True,
        domain="[('dev_is_software', '=', True)]",
        help="The project whose Backlog received the issue.")
    kind = fields.Selection(REPORT_KINDS, string="What is it?", required=True, default='bug', tracking=True)
    urgency = fields.Selection(URGENCIES, string="How urgent is it?", required=True, default='normal', tracking=True)
    description = fields.Html(
        string="Details",
        help="What happened, what you expected, and the steps to see it again.")
    reporter_id = fields.Many2one(
        'res.users', string="Reported by", required=True, readonly=True, index=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)

    state = fields.Selection(
        [('new', "New"), ('accepted', "Accepted"), ('declined', "Declined")],
        string="Decision", default='new', required=True, readonly=True, tracking=True, index=True)
    decline_reason = fields.Text(string="Why it was declined", readonly=True)
    task_id = fields.Many2one('project.task', string="Issue", readonly=True, copy=False, ondelete='set null')

    # Reporters usually can't open issues, so these are read as superuser.
    issue_key = fields.Char(string="Issue Key", compute='_compute_issue_info', compute_sudo=True)
    progress = fields.Selection(
        PROGRESS, string="Status", compute='_compute_progress', store=True, compute_sudo=True)
    done_notified = fields.Boolean(
        string="Reporter Told It's Done", readonly=True, copy=False,
        help="The reporter got the \"it's done\" message (sent only once).")

    @api.depends_context('uid')
    def _compute_allowed_app_ids(self):
        # The apps on this person's home screen (search() hides menus they can't open;
        # the Many2one dropdown alone wouldn't).
        apps = self.env['ir.ui.menu'].search([('parent_id', '=', False)])
        for report in self:
            report.allowed_app_ids = apps

    @api.depends('task_id.dev_key')
    def _compute_issue_info(self):
        for report in self:
            report.issue_key = report.task_id.dev_key

    @api.depends('state', 'task_id.dev_status')
    def _compute_progress(self):
        for report in self:
            if report.state != 'accepted':
                report.progress = report.state
            elif report.task_id.dev_status == 'done':
                report.progress = 'done'
            elif report.task_id.dev_status in ('in_progress', 'review'):
                report.progress = 'in_progress'
            else:
                report.progress = 'accepted'

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    def _check_dev_team(self):
        if not self.env.su and not self.env.user.has_group('project.group_project_user'):
            raise AccessError(_("Only the development team can accept or decline reports."))

    def write(self, vals):
        if TRIAGE_FIELDS & set(vals):
            self._check_dev_team()
        elif not self.env.su and not self.env.user.has_group('project.group_project_user') \
                and any(report.state != 'new' for report in self):
            raise UserError(_("This report was already reviewed, so it can't be changed. "
                              "Add a message below instead."))
        return super().write(vals)

    def _dev_tell_reporter(self, body):
        """A message the reporter (a follower) is notified of, signed by the
        developer. As superuser, so a developer without an email address
        can still accept or decline."""
        self.ensure_one()
        self.sudo().message_post(body=body, author_id=self.env.user.partner_id.id,
                                 message_type='comment', subtype_xmlid='mail.mt_comment')

    # ------------------------------------------------------------------
    # Triage
    # ------------------------------------------------------------------

    def action_send(self):
        """"Send" in the pop-up: the form saves first, then this thanks the
        reporter and closes the pop-up."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Thanks! The development team will review it. Follow it in My Reports."),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _issue_values(self, project):
        self.ensure_one()
        description = self.description or Markup()
        if self.app_menu_id:
            description = Markup("<p><b>%s</b> %s</p>") % (_("App:"), self.app_menu_id.sudo().name) + description
        vals = {
            'name': self.name,
            'project_id': project.id,
            'description': description,
            'dev_issue_type': KIND_TO_TYPE[self.kind],
            'dev_priority': URGENCY_TO_PRIORITY[self.urgency],
            'dev_reporter_id': self.reporter_id.id,
        }
        if self.kind == 'bug':
            vals['dev_severity'] = URGENCY_TO_SEVERITY[self.urgency]
        return vals

    def action_open_accept(self):
        """Accept: ask which project's Backlog gets the issue."""
        self._check_dev_team()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Accept Report"),
            'res_model': 'dev.report.accept',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_report_ids': self.ids},
        }

    def _accept(self, project):
        """Turn the reports into issues in the project's Backlog."""
        self._check_dev_team()
        if not project:
            raise UserError(_("Pick the project that receives the issue."))
        for report in self:
            if report.state != 'new':
                raise UserError(_("\"%s\" was already reviewed.", report.name))
            # Plain context: a new issue goes to the Backlog, outside any sprint.
            task = self.env['project.task'].with_context(
                {k: v for k, v in self.env.context.items() if not k.startswith(('default_', 'dev_'))}
            ).create(report._issue_values(project))
            attachments = self.env['ir.attachment'].search(
                [('res_model', '=', report._name), ('res_id', '=', report.id)])
            for attachment in attachments:
                attachment.copy({'res_model': 'project.task', 'res_id': task.id})
            report.write({'state': 'accepted', 'task_id': task.id, 'project_id': project.id})
            task._message_log(body=Markup(_("Created from a report by %s.")) % report.reporter_id.name)
            report._dev_tell_reporter(
                _("Accepted as %(key)s. It's in the team's Backlog now; this page shows its progress.",
                  key=task.dev_key or task.name))
        if len(self) == 1:
            return self.action_open_issue()
        return True

    def action_open_decline(self):
        self._check_dev_team()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Decline Report"),
            'res_model': 'dev.report.decline',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_report_ids': self.ids},
        }

    def _decline(self, reason):
        self._check_dev_team()
        for report in self:
            if report.state != 'new':
                raise UserError(_("\"%s\" was already reviewed.", report.name))
            report.write({'state': 'declined', 'decline_reason': reason})
            report._dev_tell_reporter(_("Declined: %s", reason))

    def _dev_tell_done(self):
        """The issue made from this report is finished: tell the reporter (once)."""
        for report in self:
            report._dev_tell_reporter(
                _("Done! %(key)s is finished. Thanks for reporting it.",
                  key=report.task_id.dev_key or report.task_id.name))
        self.sudo().write({'done_notified': True})

    def action_reopen(self):
        """Put a declined report back up for review."""
        self._check_dev_team()
        self.filtered(lambda r: r.state == 'declined').write({'state': 'new', 'decline_reason': False})

    def action_open_issue(self):
        self.ensure_one()
        if not self.task_id:
            raise UserError(_("This report has no issue."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': self.task_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }


class DevReportAccept(models.TransientModel):
    _name = 'dev.report.accept'
    _description = 'Accept Report'

    report_ids = fields.Many2many('dev.report', string="Reports", required=True)
    project_id = fields.Many2one(
        'project.project', string="Project", required=True,
        domain="[('dev_is_software', '=', True)]",
        default=lambda self: self._default_project(),
        help="The issue goes to this project's Backlog.")

    def _default_project(self):
        """The only software project, or the one that last got a report from the same app."""
        projects = self.env['project.project'].search([('dev_is_software', '=', True)], limit=2)
        if len(projects) == 1:
            return projects
        reports = self.env['dev.report'].browse(self.env.context.get('default_report_ids') or [])
        apps = reports.app_menu_id
        if len(apps) == 1:
            previous = self.env['dev.report'].search([
                ('app_menu_id', '=', apps.id), ('project_id', '!=', False)], limit=1)
            return previous.project_id
        return self.env['project.project']

    def action_confirm(self):
        self.ensure_one()
        result = self.report_ids._accept(self.project_id)
        if len(self.report_ids) == 1:
            return result
        return {'type': 'ir.actions.act_window_close'}


class DevReportDecline(models.TransientModel):
    _name = 'dev.report.decline'
    _description = 'Decline Report'

    report_ids = fields.Many2many('dev.report', string="Reports", required=True)
    reason = fields.Text(string="Reason", required=True,
                         help="The reporter sees this, so keep it friendly and clear.")

    def action_confirm(self):
        self.report_ids._decline(self.reason)
        return {'type': 'ir.actions.act_window_close'}
