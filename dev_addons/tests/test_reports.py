# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReports(TransactionCase):
    """Reports: anyone sends one from the top-bar icon, the dev team accepts
    (into a project's Backlog) or declines it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Billing', 'dev_is_software': True})
        cls.other_project = cls.env['project.project'].create({'name': 'Shop', 'dev_is_software': True})
        cls.sprint = cls.env['dev.sprint'].create({'project_id': cls.project.id})
        cls.sprint.action_start()
        employee = cls.env.ref('base.group_user')
        cls.alice = cls.env['res.users'].create({
            'name': 'Alice Sales', 'login': 'alice_reports',
            'groups_id': [(6, 0, [employee.id])]})
        cls.bob = cls.env['res.users'].create({
            'name': 'Bob Office', 'login': 'bob_reports', 'groups_id': [(6, 0, [employee.id])]})
        cls.dev = cls.env['res.users'].create({
            'name': 'Dee Dev', 'login': 'dee_reports',
            'groups_id': [(6, 0, [cls.env.ref('project.group_project_user').id])]})
        cls.discuss = cls.env.ref('base.module_mail')  # the Discuss app

    def _send(self, user=None, **vals):
        """Fill the pop-up as the reporter and click Send."""
        form = Form(self.env['dev.report'].with_user(user or self.alice),
                    view='dev_addons.report_form')
        form.name = vals.pop('name', "Can't print invoices")
        form.app_id = vals.pop('app_id', self.discuss)
        for field, value in vals.items():
            setattr(form, field, value)
        report = form.save()
        action = report.action_send()
        self.assertEqual(action['params']['next']['type'], 'ir.actions.act_window_close', "the pop-up closes")
        return report.with_env(self.env)

    def _accept(self, reports, project=None):
        action = reports.with_user(self.dev).action_open_accept()
        wizard = Form(self.env[action['res_model']].with_user(self.dev).with_context(action['context']))
        if project:
            wizard.project_id = project
        return wizard.save().action_confirm()

    def test_send_and_see_only_your_own(self):
        mine = self._send(kind='bug', urgency='blocking', app_id=self.discuss)
        self.assertEqual((mine.reporter_id, mine.state, mine.progress), (self.alice, 'new', 'new'))
        self.assertFalse(mine.project_id, "reporters don't pick a project")
        self.assertIn(self.alice.partner_id, mine.message_partner_ids, "the reporter follows it")
        theirs = self._send(user=self.bob, name='Other')
        Report = self.env['dev.report']
        self.assertEqual(Report.with_user(self.alice).search([]), mine)
        self.assertEqual(Report.with_user(self.dev).search([('id', 'in', (mine | theirs).ids)]), mine | theirs)
        with self.assertRaises(AccessError):
            theirs.with_user(self.alice).read(['name'])

    def test_reporter_form(self):
        # "Reported by" shows who it is; no Project field for reporters.
        arch = self.env['dev.report'].with_user(self.alice).get_views(
            [(self.env.ref('dev_addons.report_form').id, 'form')])['views']['form']['arch']
        self.assertIn('name="reporter_id"', arch)
        self.assertIn('name="app_id"', arch)
        self.assertNotIn('name="project_id"', arch)
        form = Form(self.env['dev.report'].with_user(self.alice), view='dev_addons.report_form')
        self.assertEqual(form.reporter_id, self.alice)
        # Apps offered: installed applications this person can open.
        dev_projects = self.env.ref('base.module_dev_addons')
        project = self.env.ref('base.module_project')
        mine = self.env['dev.report'].with_user(self.alice).new({}).allowed_app_ids._origin
        self.assertIn(self.discuss, mine)
        self.assertNotIn(dev_projects, mine, "only the dev team (and admins) report on Dev Projects")
        self.assertNotIn(project, mine)
        self.assertNotIn(self.env.ref('base.module_web'), mine, "technical modules are not apps")
        self.assertTrue(all(app.application and app.state == 'installed' for app in mine))
        devs = self.env['dev.report'].with_user(self.dev).new({}).allowed_app_ids._origin
        self.assertIn(dev_projects, devs)
        self.assertIn(project, devs)
        # Not just hidden: picking an app you can't open is refused.
        with self.assertRaises(ValidationError):
            self.env['dev.report'].with_user(self.alice).create({'name': 'Sneaky', 'app_id': dev_projects.id})

    def test_app_is_required(self):
        form = Form(self.env['dev.report'].with_user(self.alice), view='dev_addons.report_form')
        form.name = 'No app'
        with self.assertRaises(AssertionError):
            form.save()

    def test_reporter_cannot_decide(self):
        report = self._send()
        as_alice = report.with_user(self.alice)
        for call in (as_alice.action_open_accept, as_alice.action_open_decline,
                     lambda: as_alice._accept(self.project),
                     lambda: as_alice.write({'state': 'accepted'}),
                     lambda: as_alice.write({'project_id': self.project.id})):
            with self.assertRaises(AccessError):
                call()
        as_alice.write({'name': 'Still editable while new'})

    def test_accept_makes_a_backlog_issue(self):
        report = self._send(kind='bug', urgency='high', description='<p>The button is grey</p>',
                            app_id=self.discuss)
        self.env['ir.attachment'].create({
            'name': 'screen.png', 'datas': base64.b64encode(b'png'),
            'res_model': 'dev.report', 'res_id': report.id})
        action = self._accept(report, self.project)
        issue = report.task_id
        self.assertEqual(action['res_id'], issue.id, "opens the new issue")
        self.assertEqual((report.state, report.project_id), ('accepted', self.project))
        self.assertEqual(issue.project_id, self.project)
        self.assertEqual((issue.dev_issue_type, issue.dev_priority, issue.dev_severity), ('bug', '2', 'major'))
        self.assertEqual(issue.dev_reporter_id, self.alice, "the reporter is 'Reported by'")
        self.assertFalse(issue.dev_sprint_id, "goes to the Backlog even with a running sprint")
        self.assertIn('grey', str(issue.description))
        self.assertIn(self.discuss.shortdesc, str(issue.description), "the issue says which app")
        self.assertTrue(issue.dev_key)
        self.assertEqual(self.env['ir.attachment'].search_count(
            [('res_model', '=', 'project.task'), ('res_id', '=', issue.id)]), 1, "screenshots come along")
        # The reporter can't open issues but still sees the key and progress.
        as_alice = report.with_user(self.alice)
        self.assertEqual((as_alice.issue_key, as_alice.progress), (issue.dev_key, 'accepted'))
        issue.stage_id = self.env.ref('dev_addons.stage_in_progress')
        self.assertEqual(as_alice.progress, 'in_progress')
        told = report.message_ids
        issue.stage_id = self.env.ref('dev_addons.stage_done')
        self.assertEqual(as_alice.progress, 'done')
        # The reporter is told it's done, once (even if it's reopened and done again).
        done_messages = (report.message_ids - told).filtered(lambda m: 'is finished' in (m.body or ''))
        self.assertEqual(len(done_messages), 1)
        self.assertIn(issue.dev_key, done_messages.body)
        self.assertTrue(report.done_notified)
        issue.stage_id = self.env.ref('dev_addons.stage_in_progress')
        issue.stage_id = self.env.ref('dev_addons.stage_done')
        self.assertEqual(len(report.message_ids.filtered(lambda m: 'is finished' in (m.body or ''))), 1)
        with self.assertRaises(UserError):
            as_alice.write({'name': 'Changed after review'})
        with self.assertRaises(UserError):
            report.with_user(self.dev)._accept(self.project)

    def test_accept_suggests_the_project(self):
        first = self._send(app_id=self.discuss)
        self._accept(first, self.other_project)
        # Next report from the same app: the same project is suggested.
        second = self._send(name='Again', app_id=self.discuss)
        action = second.with_user(self.dev).action_open_accept()
        wizard = Form(self.env[action['res_model']].with_user(self.dev).with_context(action['context']))
        self.assertEqual(wizard.project_id, self.other_project)

    def test_kinds_become_issue_types(self):
        feature = self._send(kind='feature', urgency='low')
        question = self._send(kind='question', urgency='blocking')
        self._accept(feature | question, self.project)
        self.assertEqual(feature.task_id.dev_issue_type, 'story')
        self.assertEqual((question.task_id.dev_issue_type, question.task_id.dev_priority), ('task', '3'))
        # Several at once from the list (Actions > Accept).
        more = self._send(name='One') | self._send(name='Two')
        action = self.env.ref('dev_addons.action_report_accept_server').with_user(self.dev).with_context(
            active_model='dev.report', active_ids=more.ids).run()
        self.assertEqual((action['res_model'], action['context']['default_report_ids']), ('dev.report.accept', more.ids))

    def test_decline_with_reason_and_review_again(self):
        report = self._send()
        action = report.with_user(self.dev).action_open_decline()
        wizard = Form(self.env[action['res_model']].with_user(self.dev).with_context(action['context']))
        wizard.reason = 'Use File > Print instead.'
        wizard.save().action_confirm()
        self.assertEqual((report.state, report.progress, report.decline_reason),
                         ('declined', 'declined', 'Use File > Print instead.'))
        self.assertIn('Use File &gt; Print instead.', report.message_ids[0].body)
        self.assertFalse(report.task_id)
        report.with_user(self.dev).action_reopen()
        self.assertEqual((report.state, report.decline_reason), ('new', False))

    def test_top_bar_icon_actions(self):
        # The icon opens these two: the form as a pop-up, and the reporter's own list.
        new = self.env.ref('dev_addons.action_report_new')
        self.assertEqual((new.res_model, new.target, new.view_mode), ('dev.report', 'new', 'form'))
        mine = self.env.ref('dev_addons.action_report_mine')
        self.assertEqual(mine.domain, "[('reporter_id', '=', uid)]")
        # No Report menu any more, and the Projects app is for the dev team only.
        self.assertFalse(self.env.ref('dev_addons.menu_report_root', raise_if_not_found=False))
        visible = self.env['ir.ui.menu'].with_user(self.alice)._visible_menu_ids()
        self.assertNotIn(self.env.ref('project.menu_main_pm').id, visible)
