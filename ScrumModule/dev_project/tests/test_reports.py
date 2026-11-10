# -*- coding: utf-8 -*-
from datetime import timedelta

from lxml import etree

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestTickets(TransactionCase):
    """Tickets: anyone sends one from the top-bar icon; the team (devs and IT)
    works them on their own board. They never go into projects or Backlogs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Billing', 'dev_is_software': True})
        employee = cls.env.ref('base.group_user')
        team = cls.env.ref('project.group_project_user')
        cls.alice = cls.env['res.users'].create({
            'name': 'Alice Sales', 'login': 'alice_tickets', 'groups_id': [(6, 0, [employee.id])]})
        cls.bob = cls.env['res.users'].create({
            'name': 'Bob Office', 'login': 'bob_tickets', 'groups_id': [(6, 0, [employee.id])]})
        cls.dev = cls.env['res.users'].create({
            'name': 'Dee Dev', 'login': 'dee_tickets', 'groups_id': [(6, 0, [team.id])]})
        cls.it = cls.env['res.users'].create({
            'name': 'Ian IT', 'login': 'ian_tickets', 'groups_id': [(6, 0, [team.id])]})
        cls.discuss = cls.env.ref('base.module_mail')  # the Discuss app

    def _send(self, user=None, **vals):
        """Fill the pop-up as the reporter and click Send."""
        form = Form(self.env['dev.report'].with_user(user or self.alice), view='dev_addons.report_form')
        form.name = vals.pop('name', "Can't print invoices")
        form.topic = vals.pop('topic', 'app')
        if form.topic == 'app':
            form.app_id = vals.pop('app_id', self.discuss)
        for field, value in vals.items():
            setattr(form, field, value)
        ticket = form.save()
        action = ticket.action_send()
        self.assertEqual(action['params']['next']['type'], 'ir.actions.act_window_close', "the pop-up closes")
        self.assertIn(ticket.key, action['params']['message'])
        return ticket.with_env(self.env)

    def _said(self, ticket, text):
        return ticket.message_ids.filtered(lambda m: text in (m.body or ''))

    # Sending -------------------------------------------------------------

    def test_send_and_see_only_your_own(self):
        mine = self._send(kind='bug', urgency='blocking')
        self.assertTrue(mine.key.startswith('TCK-'))
        self.assertEqual(mine.display_name, f"{mine.key} Can't print invoices")
        self.assertEqual((mine.reporter_id, mine.state, mine.progress), (self.alice, 'new', 'new'))
        self.assertIn(self.alice.partner_id, mine.message_partner_ids, "the reporter follows it")
        theirs = self._send(user=self.bob, name='Other')
        self.assertNotEqual(mine.key, theirs.key)
        Ticket = self.env['dev.report']
        self.assertEqual(Ticket.with_user(self.alice).search([]), mine)
        self.assertEqual(Ticket.with_user(self.it).search([('id', 'in', (mine | theirs).ids)]), mine | theirs)
        with self.assertRaises(AccessError):
            theirs.with_user(self.alice).read(['name'])

    def test_it_or_app(self):
        it = self._send(topic='it', name='Printer jammed')
        self.assertEqual((it.topic, it.app_id), ('it', self.env['ir.module.module']))
        # An app ticket needs its app; an IT one doesn't.
        form = Form(self.env['dev.report'].with_user(self.alice), view='dev_addons.report_form')
        form.name = 'No app'
        with self.assertRaises(AssertionError):
            form.save()
        form.topic = 'it'
        form.save()
        # Switching to IT drops the app.
        ticket = self.env['dev.report'].with_user(self.alice).create(
            {'name': 'Was app', 'topic': 'app', 'app_id': self.discuss.id})
        ticket.write({'topic': 'it'})
        self.assertFalse(ticket.app_id)

    def _app_dropdown(self, user):
        """What the App dropdown lists for this person: the form's own domain
        and context on a brand-new ticket, searched like the browser does."""
        Ticket = self.env['dev.report'].with_user(user)
        arch = Ticket.get_views([(self.env.ref('dev_addons.report_form').id, 'form')])['views']['form']['arch']
        node = etree.fromstring(arch).find(".//field[@name='app_id']")
        context = safe_eval(node.get('context') or '{}')
        domain = Ticket.fields_get(['app_id'])['app_id']['domain']
        if isinstance(domain, str):
            domain = safe_eval(domain, {})  # a string domain would need the form's values
        found = self.env['ir.module.module'].with_user(user).with_context(**context).name_search('', domain, limit=100)
        return self.env['ir.module.module'].browse([app_id for app_id, _name in found])

    def test_apps_by_access(self):
        dev_projects = self.env.ref('base.module_dev_addons')
        project = self.env.ref('base.module_project')
        mine = self._app_dropdown(self.alice)
        self.assertIn(self.discuss, mine, "the list is never empty for a new ticket")
        self.assertNotIn(dev_projects, mine, "only the team (and admins) report on Dev Projects")
        self.assertNotIn(project, mine)
        self.assertNotIn(self.env.ref('base.module_web'), mine, "technical modules are not apps")
        self.assertTrue(all(app.application and app.state == 'installed' for app in mine))
        team = self._app_dropdown(self.dev)
        self.assertIn(dev_projects, team)
        self.assertIn(project, team)
        # Other searches on apps (e.g. the Apps screen) are not filtered.
        self.assertIn(dev_projects, self.env['ir.module.module'].with_user(self.alice).search([('application', '=', True)]))
        with self.assertRaises(ValidationError):
            self.env['dev.report'].with_user(self.alice).create({'name': 'Sneaky', 'app_id': dev_projects.id})

    def test_form_shows_who_and_steps(self):
        arch = self.env['dev.report'].with_user(self.alice).get_views(
            [(self.env.ref('dev_addons.report_form').id, 'form')])['views']['form']['arch']
        for name in ('reporter_id', 'topic', 'app_id', 'kind', 'urgency', 'description'):
            self.assertIn(f'name="{name}"', arch)
        self.assertNotIn('name="user_id"', arch, "assigning is for the team")
        self.assertIn('Tell us how to see the problem', arch)
        self.assertEqual(Form(self.env['dev.report'].with_user(self.alice)).reporter_id, self.alice)

    # The team's board ----------------------------------------------------

    def test_board_flow_never_touches_projects(self):
        tasks_before = self.env['project.task'].search_count([])
        ticket = self._send()
        ticket.with_user(self.dev).action_accept()
        self.assertEqual((ticket.state, ticket.progress), ('todo', 'accepted'))
        self.assertTrue(self._said(ticket, 'Accepted:'))
        ticket.with_user(self.it).action_start()
        self.assertEqual((ticket.state, ticket.user_id), ('in_progress', self.it), "whoever starts it takes it")
        self.assertEqual(ticket.with_user(self.alice).progress, 'in_progress')
        ticket.with_user(self.it).action_done()
        self.assertEqual((ticket.state, ticket.progress), ('done', 'done'))
        self.assertTrue(ticket.done_date)
        self.assertEqual(len(self._said(ticket, 'Done!')), 1)
        self.assertEqual(self.env['project.task'].search_count([]), tasks_before, "no issues, no Backlog")
        with self.assertRaises(UserError):
            ticket.with_user(self.alice).write({'name': 'Changed after review'})

    def test_dragging_on_the_board(self):
        ticket = self._send()
        ticket.with_user(self.dev).write({'state': 'in_progress'})  # New straight to In Progress
        self.assertEqual(ticket.user_id, self.dev)
        self.assertTrue(self._said(ticket, 'Accepted:'), "the reporter is still told")
        ticket.with_user(self.it).action_assign_to_me()
        self.assertEqual(ticket.user_id, self.it)
        groups = self.env['dev.report'].with_user(self.dev).read_group([], ['state'], ['state'])
        self.assertEqual([g['state'] for g in groups], ['new', 'todo', 'in_progress', 'done'],
                         "the board always shows its four columns")

    def test_most_urgent_first(self):
        normal = self._send(name='Normal', urgency='normal')
        blocking = self._send(name='Blocking', urgency='blocking')
        low = self._send(name='Low', urgency='low')
        found = self.env['dev.report'].search([('id', 'in', (normal | blocking | low).ids)])
        self.assertEqual(found.mapped('name'), ['Blocking', 'Normal', 'Low'])

    def test_reporter_cannot_handle_tickets(self):
        ticket = self._send()
        as_alice = ticket.with_user(self.alice)
        for call in (as_alice.action_accept, as_alice.action_start, as_alice.action_done,
                     as_alice.action_assign_to_me, as_alice.action_open_decline,
                     lambda: as_alice.write({'state': 'todo'}),
                     lambda: as_alice.write({'user_id': self.dev.id})):
            with self.assertRaises(AccessError):
                call()
        as_alice.write({'name': 'Still editable while new'})

    def test_decline_with_reason_and_review_again(self):
        ticket = self._send()
        action = ticket.with_user(self.dev).action_open_decline()
        wizard = Form(self.env[action['res_model']].with_user(self.dev).with_context(action['context']))
        wizard.reason = 'Use File > Print instead.'
        wizard.save().action_confirm()
        self.assertEqual((ticket.state, ticket.progress, ticket.decline_reason),
                         ('declined', 'declined', 'Use File > Print instead.'))
        self.assertIn('Use File &gt; Print instead.', ticket.message_ids[0].body)
        ticket.with_user(self.dev).action_review_again()
        self.assertEqual((ticket.state, ticket.decline_reason), ('new', False))

    def test_mass_accept(self):
        tickets = self._send(name='One') | self._send(name='Two')
        self.env.ref('dev_addons.action_report_accept_server').with_user(self.dev).with_context(
            active_model='dev.report', active_ids=tickets.ids).run()
        self.assertEqual(set(tickets.mapped('state')), {'todo'})

    # Reporter says "still not fixed" ---------------------------------------

    def test_still_not_fixed(self):
        ticket = self._send()
        ticket.with_user(self.it).action_start()
        ticket.with_user(self.it).action_done()
        self.assertTrue(ticket.with_user(self.alice).can_reopen)
        self.assertFalse(ticket.with_user(self.it).can_reopen, "only the person who sent it")
        action = ticket.with_user(self.alice).action_open_reopen()
        wizard = Form(self.env[action['res_model']].with_user(self.alice).with_context(action['context']))
        wizard.comment = 'Only prints one page'
        wizard.save().action_confirm()
        self.assertEqual((ticket.state, ticket.progress), ('todo', 'accepted'))
        said = self._said(ticket, 'Still not fixed: Only prints one page')
        self.assertEqual(said.author_id, self.alice.partner_id)
        self.assertIn(self.it.partner_id, said.partner_ids, "the person handling it is told")
        # Done again; after the reopen window it can't be sent back.
        ticket.with_user(self.it).action_done()
        self.assertEqual(len(self._said(ticket, 'Done!')), 2)
        ticket.sudo().write({'done_date': fields.Datetime.now() - timedelta(days=8)})
        ticket.invalidate_recordset(['can_reopen'])
        self.assertFalse(ticket.with_user(self.alice).can_reopen)
        with self.assertRaises(UserError):
            ticket.with_user(self.alice).action_open_reopen()

    # Telling the team -----------------------------------------------------

    def test_urgent_tickets_notify_the_team(self):
        def notices(ticket):
            return self.env['mail.message'].search([
                ('model', '=', 'dev.report'), ('res_id', '=', ticket.id),
                ('message_type', '=', 'user_notification')])

        urgent = self._send(name='Server down', urgency='blocking')
        notice = notices(urgent)
        self.assertTrue(notice)
        self.assertIn(self.dev.partner_id, notice.partner_ids)
        self.assertIn(self.it.partner_id, notice.partner_ids)
        self.assertNotIn(self.alice.partner_id, notice.partner_ids)
        calm = self._send(name='Whenever', urgency='low')
        self.assertFalse(notices(calm))

    # Screens ----------------------------------------------------------------

    def test_menus_and_actions(self):
        menu = self.env.ref('dev_addons.menu_tickets')
        self.assertEqual(menu.parent_id, self.env.ref('dev_addons.menu_work'))
        self.assertEqual(self.env.ref('dev_addons.menu_work').child_id.mapped('name'), ['Board', 'Backlog', 'Tickets'])
        self.assertFalse(self.env.ref('dev_addons.menu_reports_triage', raise_if_not_found=False))
        new = self.env.ref('dev_addons.action_report_new')
        self.assertEqual((new.name, new.target), ('New Ticket', 'new'))
        self.assertEqual(self.env.ref('dev_addons.action_report_mine').name, 'My Tickets')
        visible = self.env['ir.ui.menu'].with_user(self.alice)._visible_menu_ids()
        self.assertNotIn(self.env.ref('project.menu_main_pm').id, visible)
