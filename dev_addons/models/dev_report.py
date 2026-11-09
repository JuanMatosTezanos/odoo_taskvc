# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression

TOPICS = [
    ('app', "An Odoo app"),
    ('it', "IT Support"),
]

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
URGENCY_LEVEL = {'low': 0, 'normal': 1, 'high': 2, 'blocking': 3}

# The ticket board's columns (Declined is kept off the board).
STAGES = [
    ('new', "New"),
    ('todo', "To Do"),
    ('in_progress', "In Progress"),
    ('done', "Done"),
    ('declined', "Declined"),
]
BOARD_STAGES = ['new', 'todo', 'in_progress', 'done']

# What the reporter sees, in order.
PROGRESS = [
    ('new', "Waiting for review"),
    ('accepted', "Accepted"),
    ('in_progress', "Being worked on"),
    ('done', "Done"),
    ('declined', "Declined"),
]
STAGE_TO_PROGRESS = {'new': 'new', 'todo': 'accepted', 'in_progress': 'in_progress',
                     'done': 'done', 'declined': 'declined'}

# How long the reporter can say "Still not fixed" after a ticket is done.
REOPEN_DAYS = 7

# Only the team (devs and IT) moves and assigns tickets.
TEAM_FIELDS = {'state', 'decline_reason', 'user_id', 'key', 'done_date'}


class DevReport(models.Model):
    """A ticket: something a person outside the team sends from the top-bar
    icon (a problem in an Odoo app, an IT problem, a wish or a question).
    Tickets live on their own board (Dev Projects > Work > Tickets) and never
    go into projects, Backlogs or sprints."""
    _name = 'dev.report'
    _description = 'Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'urgency_level desc, create_date, id'
    _rec_names_search = ['name', 'key']

    key = fields.Char(string="Ticket", readonly=True, copy=False, index=True,
                      help="The ticket's number, e.g. TCK-12.")
    name = fields.Char(string="Title", required=True, tracking=True,
                       help="In a few words, e.g. \"Can't print invoices\".")
    topic = fields.Selection(TOPICS, string="What's it about?", required=True, default='app', tracking=True)
    # An installed application (Sales, Inventory, Dev Projects...) that this
    # person can actually open: no reporting on apps they have no access to.
    # The dropdown passes 'dev_ticket_apps', and ir.module.module's search keeps
    # only those apps (see IrModuleModule below).
    app_id = fields.Many2one(
        'ir.module.module', string="App", tracking=True, ondelete='set null', index=True,
        domain=[('application', '=', True), ('state', '=', 'installed')],
        context={'dev_ticket_apps': True},
        help="The Odoo app where it happens, e.g. Sales or Inventory.")
    kind = fields.Selection(REPORT_KINDS, string="What is it?", required=True, default='bug', tracking=True)
    urgency = fields.Selection(URGENCIES, string="How urgent is it?", required=True, default='normal', tracking=True)
    urgency_level = fields.Integer(compute='_compute_urgency_level', store=True)
    description = fields.Html(string="Details")
    reporter_id = fields.Many2one(
        'res.users', string="Reported by", required=True, readonly=True, index=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)

    state = fields.Selection(
        STAGES, string="Stage", default='new', required=True, tracking=True, index=True,
        group_expand='_group_expand_states')
    user_id = fields.Many2one(
        'res.users', string="Assigned to", tracking=True, index=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('project.group_project_user').id),
                             ('share', '=', False)],
        help="Who on the team (devs and IT) is handling it.")
    decline_reason = fields.Text(string="Why it was declined", readonly=True)
    done_date = fields.Datetime(string="Done On", readonly=True, copy=False)
    progress = fields.Selection(PROGRESS, string="Status", compute='_compute_progress', store=True)
    can_reopen = fields.Boolean(compute='_compute_can_reopen')

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends('urgency')
    def _compute_urgency_level(self):
        for ticket in self:
            ticket.urgency_level = URGENCY_LEVEL.get(ticket.urgency, 1)

    @api.depends('state')
    def _compute_progress(self):
        for ticket in self:
            ticket.progress = STAGE_TO_PROGRESS[ticket.state]

    @api.depends('key', 'name')
    def _compute_display_name(self):
        for ticket in self:
            ticket.display_name = f"{ticket.key} {ticket.name}" if ticket.key else ticket.name

    @api.depends_context('uid')
    @api.depends('state', 'done_date', 'reporter_id')
    def _compute_can_reopen(self):
        limit = fields.Datetime.now() - timedelta(days=REOPEN_DAYS)
        for ticket in self:
            ticket.can_reopen = (ticket.state == 'done' and ticket.reporter_id == self.env.user
                                 and bool(ticket.done_date) and ticket.done_date >= limit)

    @api.model
    def _group_expand_states(self, states, domain, order):
        return BOARD_STAGES

    @api.model
    def _dev_apps_for_user(self):
        """Installed applications the current user can open (e.g. Dev Projects
        only for the dev team). An app counts when the user can reach one of
        its menus, or sees a home-screen icon that belongs to it (Sales' menus
        come from the "sale" module, but its icon is the Sales app's)."""
        apps = self.env['ir.module.module'].sudo().with_context(dev_ticket_apps=False).search(
            [('application', '=', True), ('state', '=', 'installed')])
        visible = self.env['ir.ui.menu']._visible_menu_ids()
        # A menu inside a hidden menu (e.g. inside the Projects app for a
        # non-developer) can't be reached: every menu above it must be visible too.
        menus = self.env['ir.ui.menu'].sudo().browse(visible)
        reachable = menus.filtered(lambda menu: all(
            int(pid) in visible for pid in (menu.parent_path or '').split('/') if pid))
        data = self.env['ir.model.data'].sudo().search_read([
            ('model', '=', 'ir.ui.menu'), ('module', 'in', apps.mapped('name')),
            ('res_id', 'in', reachable.ids),
        ], ['module'])
        names = {row['module'] for row in data}
        names |= {menu.web_icon.split(',')[0] for menu in reachable
                  if not menu.parent_id and menu.web_icon}
        return apps.filtered(lambda app: app.name in names).with_env(self.env)

    @api.constrains('app_id')
    def _check_app_access(self):
        if self.env.su:
            return
        apps = self._dev_apps_for_user()
        for ticket in self:
            if ticket.app_id and ticket.app_id not in apps:
                raise ValidationError(_("You can only report on apps you have access to."))

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    def _is_team(self):
        return self.env.su or self.env.user.has_group('project.group_project_user')

    def _check_team(self):
        if not self._is_team():
            raise AccessError(_("Only the team (devs and IT) can handle tickets."))

    @api.model
    def _team_partners(self):
        group = self.env.ref('project.group_project_user')
        return group.sudo().users.filtered(lambda u: u.active and not u.share).partner_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('topic') == 'it':
                vals['app_id'] = False
        tickets = super().create(vals_list)
        for ticket in tickets.sudo():
            ticket.key = self.env['ir.sequence'].sudo().next_by_code('dev.ticket')
            team = self._team_partners() - ticket.reporter_id.partner_id
            if ticket.urgency in ('high', 'blocking') and team:
                # Urgent ones shouldn't sit unseen: notify the whole team.
                ticket.message_notify(
                    partner_ids=team.ids,
                    author_id=ticket.reporter_id.partner_id.id,
                    subject=_("Urgent ticket %s", ticket.key),
                    body=_("%(who)s sent an urgent ticket: %(title)s (%(urgency)s).",
                           who=ticket.reporter_id.name, title=ticket.name,
                           urgency=dict(URGENCIES)[ticket.urgency]))
        return tickets

    def write(self, vals):
        if TEAM_FIELDS & set(vals):
            self._check_team()
        elif not self._is_team() and any(ticket.state != 'new' for ticket in self):
            raise UserError(_("This ticket was already reviewed, so it can't be changed. "
                              "Add a message below instead."))
        if vals.get('topic') == 'it':
            vals = dict(vals, app_id=False)
        old_states = {ticket.id: ticket.state for ticket in self}
        new_state = vals.get('state')
        if new_state == 'done':
            vals = dict(vals, done_date=fields.Datetime.now())
        res = super().write(vals)
        if new_state:
            self._after_stage_change(old_states, new_state)
        return res

    def _after_stage_change(self, old_states, new_state):
        for ticket in self:
            old = old_states[ticket.id]
            if old == new_state:
                continue
            if new_state == 'in_progress' and not ticket.user_id and not self.env.su:
                ticket.user_id = self.env.user  # whoever starts it takes it
            if old == 'new' and new_state in ('todo', 'in_progress', 'done'):
                ticket._dev_tell_reporter(
                    _("Accepted: %s is on the team's list now. This page shows its progress.", ticket.key))
            if new_state == 'done':
                ticket._dev_tell_reporter(
                    _("Done! %s is finished. Thanks for reporting it. If it's still not fixed, "
                      "click \"Still not fixed\" within %s days.", ticket.key, REOPEN_DAYS))

    def _dev_tell_reporter(self, body):
        """A message the reporter (a follower) is notified of, signed by the
        team member. As superuser, so someone without an email address can
        still handle tickets."""
        self.ensure_one()
        self.sudo().message_post(body=body, author_id=self.env.user.partner_id.id,
                                 message_type='comment', subtype_xmlid='mail.mt_comment')

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def action_send(self):
        """"Send" in the pop-up: the form saves first, then this thanks the
        reporter and closes the pop-up."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Thanks! Your ticket %s was sent. Follow it in My Tickets.", self.key),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_accept(self):
        self._check_team()
        if any(ticket.state != 'new' for ticket in self):
            raise UserError(_("Only new tickets can be accepted."))
        self.write({'state': 'todo'})

    def action_start(self):
        self._check_team()
        self.write({'state': 'in_progress'})

    def action_done(self):
        self._check_team()
        self.write({'state': 'done'})

    def action_assign_to_me(self):
        self._check_team()
        self.write({'user_id': self.env.user.id})

    def action_open_decline(self):
        self._check_team()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Decline Ticket"),
            'res_model': 'dev.report.decline',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_report_ids': self.ids},
        }

    def _decline(self, reason):
        self._check_team()
        for ticket in self:
            if ticket.state != 'new':
                raise UserError(_("Only new tickets can be declined (\"%s\" was already accepted).", ticket.name))
            ticket.write({'state': 'declined', 'decline_reason': reason})
            ticket._dev_tell_reporter(_("Declined: %s", reason))

    def action_review_again(self):
        """Put a declined ticket back in New."""
        self._check_team()
        self.filtered(lambda t: t.state == 'declined').write({'state': 'new', 'decline_reason': False})

    def action_open_reopen(self):
        self.ensure_one()
        if not self.can_reopen:
            raise UserError(_("Only the person who sent it can reopen it, within %s days of it being done.", REOPEN_DAYS))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Still not fixed"),
            'res_model': 'dev.report.reopen',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_report_id': self.id},
        }

    def _reopen(self, comment):
        """The reporter says it's still not fixed: back to To Do, with their comment."""
        self.ensure_one()
        if not self.can_reopen:
            raise UserError(_("Only the person who sent it can reopen it, within %s days of it being done.", REOPEN_DAYS))
        reporter = self.env.user
        ticket = self.sudo()
        super(DevReport, ticket).write({'state': 'todo', 'done_date': False})
        ticket.message_post(
            body=_("Still not fixed: %s", comment), author_id=reporter.partner_id.id,
            message_type='comment', subtype_xmlid='mail.mt_comment',
            partner_ids=(ticket.user_id.partner_id or self._team_partners()).ids)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.model
    def _search(self, domain, *args, **kwargs):
        # The ticket form's App dropdown: only apps this person can open.
        if self.env.context.get('dev_ticket_apps'):
            allowed = self.env['dev.report']._dev_apps_for_user()
            domain = expression.AND([domain or [], [('id', 'in', allowed.ids)]])
        return super()._search(domain, *args, **kwargs)


class DevReportDecline(models.TransientModel):
    _name = 'dev.report.decline'
    _description = 'Decline Ticket'

    report_ids = fields.Many2many('dev.report', string="Tickets", required=True)
    reason = fields.Text(string="Reason", required=True,
                         help="The person who sent it sees this, so keep it friendly and clear.")

    def action_confirm(self):
        self.report_ids._decline(self.reason)
        return {'type': 'ir.actions.act_window_close'}


class DevReportReopen(models.TransientModel):
    _name = 'dev.report.reopen'
    _description = 'Reopen Ticket'

    report_id = fields.Many2one('dev.report', string="Ticket", required=True)
    comment = fields.Text(string="What's still wrong?", required=True)

    def action_confirm(self):
        self.report_id._reopen(self.comment)
        return {'type': 'ir.actions.act_window_close'}
