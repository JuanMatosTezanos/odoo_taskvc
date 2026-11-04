# -*- coding: utf-8 -*-
from datetime import timedelta

from lxml import etree
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger
from odoo.tools.safe_eval import safe_eval

from odoo.addons.manage_plus.hooks import migrate_to_issues


@tagged('post_install', '-at_install')
class TestManagePlus(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.now = fields.Datetime.now()
        cls.Issue = cls.env['manage.task']
        cls.project = cls.env['manage.project'].create({'name': 'Web Shop'})
        cls.history = cls.env['manage.history'].create({'name': 'Login', 'project': cls.project.id})
        cls.sprint = cls.env['manage.sprint'].create({
            'name': 'S1', 'project': cls.project.id, 'duration': 14})
        cls.dev = cls.env['res.partner'].create({
            'name': 'Dev Plus', 'is_dev': True, 'access_level': '11112222a'})
        cls.dev2 = cls.env['res.partner'].create({
            'name': 'Dev Two', 'is_dev': True, 'access_level': '33334444b'})
        cls.stage_todo = cls.env.ref('manage_plus.stage_todo')
        cls.stage_progress = cls.env.ref('manage_plus.stage_in_progress')
        cls.stage_done = cls.env.ref('manage_plus.stage_done')

    def _issue(self, **vals):
        return self.Issue.create(dict({'name': 'T', 'project': self.project.id}, **vals))

    # Keys ---------------------------------------------------------------

    def test_project_keys(self):
        self.assertEqual(self.project.key, 'WS')
        a, b = self._issue(), self._issue(history=self.history.id)
        self.assertEqual((a.key, b.key), ('WS-1', 'WS-2'))
        self.assertEqual(a.display_name, '[WS-1] T')
        self.assertEqual(self.Issue.search([('code', '=', 'WS-2')]), b)
        self.assertIn(a.id, [r[0] for r in self.Issue.name_search('WS-1')])
        # Moving to another project gives a key from that project.
        other = self.env['manage.project'].create({'name': 'Api', 'key': 'api'})
        self.assertEqual(other.key, 'API')
        a.project = other
        self.assertEqual(a.key, 'API-1')
        with self.assertRaises(UserError):
            self.project.key = 'NEW'
        with self.assertRaises(ValidationError):
            self.env['manage.project'].create({'name': 'Bad', 'key': '1X'})

    def test_project_without_history(self):
        issue = self._issue()
        self.assertEqual(issue.project, self.project)
        issue.history = self.history
        self.assertEqual(issue.project, self.project)
        with self.assertRaises(ValidationError):
            other = self.env['manage.project'].create({'name': 'Other'})
            self._issue(project=other.id, history=self.history.id)

    # Stages ------------------------------------------------------------

    def test_stage_and_state_stay_in_sync(self):
        issue = self._issue()
        self.assertEqual(issue.stage_id, self.stage_todo)
        issue.stage_id = self.stage_progress  # kanban drag
        self.assertEqual(issue.state, 'in_progress')
        self.assertTrue(issue.start_date)
        issue.action_done()  # button writes the state
        self.assertEqual(issue.stage_id, self.stage_done)
        self.assertTrue(issue.end_date)
        qa = self.env['manage.stage'].create({'name': 'QA', 'state': 'review', 'sequence': 25})
        issue.stage_id = qa
        self.assertEqual(issue.state, 'review')
        self.assertFalse(issue.end_date)

    def test_wip_limit(self):
        self.stage_progress.wip_limit = 1
        self._issue(sprint=self.sprint.id, stage_id=self.stage_progress.id)
        second = self._issue(sprint=self.sprint.id)
        with self.assertRaises(UserError):
            second.stage_id = self.stage_progress
        # Other sprints have their own count.
        second.sprint = False
        second.stage_id = self.stage_progress

    # Assignee / reporter -----------------------------------------------

    def test_assignee_reporter_and_team(self):
        issue = self._issue(assignee=self.dev.id)
        self.assertEqual(issue.reporter_id, self.env.user)
        self.assertEqual(issue.developer, self.dev)
        issue.assignee = self.dev2
        self.assertEqual(issue.developer, self.dev | self.dev2)
        self.assertEqual(self.dev2.open_item_count, 1)
        from_dev = self.Issue.with_context(current_developer=self.dev.id).create({'name': 'X'})
        self.assertEqual(from_dev.assignee, self.dev)

    # Sprints -----------------------------------------------------------

    def test_sprint_start_and_complete(self):
        nxt = self.env['manage.sprint'].create({'project': self.project.id, 'duration': 14})
        done = self._issue(sprint=self.sprint.id, story_points=3)
        open_ = self._issue(sprint=self.sprint.id, story_points=5)
        backlog = self._issue()
        done.action_done()
        self.assertEqual(self.sprint.state, 'planned')
        self.assertFalse(backlog.sprint, "new issues go to the backlog")

        self.sprint.action_start()
        self.assertEqual(self.sprint.state, 'running')
        self.assertTrue(self.sprint.start_date)
        with self.assertRaises(ValidationError):
            nxt.action_start()  # one running sprint per project
        self.assertEqual(self.sprint.progress, 50.0)
        self.assertEqual((self.sprint.planned_points, self.sprint.done_points), (8, 3))

        wizard = Form(self.env['manage.sprint.complete'].with_context(default_sprint_id=self.sprint.id))
        self.assertEqual(wizard.destination, 'sprint')
        self.assertEqual(wizard.target_sprint_id, nxt)
        wizard.save().action_confirm()
        self.assertEqual(self.sprint.state, 'closed')
        self.assertEqual(open_.sprint, nxt)
        self.assertEqual(done.sprint, self.sprint, "finished work stays in its sprint")
        self.assertTrue(self.sprint.active, "closed sprints are not archived")

    def _search_filter_domain(self, filter_name):
        arch = self.Issue.get_views([(False, 'search')])['views']['search']['arch']
        node = etree.fromstring(arch).find(f".//filter[@name='{filter_name}']")
        return safe_eval(node.get('domain'), {'uid': self.env.uid})

    def test_board_shows_current_work(self):
        board = self.env.ref('manage.action_task_window')
        ctx = safe_eval(board.context)
        self.assertEqual(ctx.get('search_default_current_work'), 1, "board opens on current work")
        self.assertFalse(self.env.ref('manage.menu_1_bug_list').active)
        self.assertEqual(self.env.ref('manage.menu_1_task_list').name, 'Board')
        domain = self._search_filter_domain('current_work')
        loose = self._issue()
        planned_elsewhere = self._issue(sprint=self.sprint.id)
        on_board = self.Issue.search(domain)
        self.assertIn(loose, on_board, "issues without a sprint show on the board")
        self.assertNotIn(planned_elsewhere, on_board, "planned sprints are not on the board")

        self.sprint.action_start()
        created = self.Issue.with_context(**ctx).create({'name': 'From board', 'project': self.project.id})
        self.assertEqual(created.sprint, self.sprint, "created on the board: goes into the running sprint")
        self.assertIn(created, self.Issue.search(domain))
        self.assertIn(planned_elsewhere, self.Issue.search(domain))
        # With a default project from the context (e.g. opened from a project).
        other = self.Issue.with_context(default_project=self.project.id, **ctx).create({'name': 'Ctx'})
        self.assertEqual((other.project, other.sprint), (self.project, self.sprint))

    def test_complete_archive_and_delete(self):
        self.sprint.action_start()
        keep = self._issue(sprint=self.sprint.id, story_points=2)
        drop = self._issue(sprint=self.sprint.id, story_points=1)
        other = self._issue()
        self.assertEqual(self.project.task_count, 3)

        action = keep.action_open_complete_wizard()
        wizard = Form(self.env[action['res_model']].with_context(**action['context']))
        self.assertEqual(wizard.mode, 'archive')
        result = wizard.save().action_confirm()
        self.assertEqual(result['res_model'], 'manage.task', "goes back to the board")
        self.assertEqual((keep.state, keep.active), ('done', False))
        self.assertTrue(keep.end_date)
        self.assertNotIn(keep, self.Issue.search([]), "archived issues leave the board")
        self.assertIn(keep, self.Issue.search(self._search_filter_domain('archived')))

        # From the list's Action menu (active_ids), deleting.
        wizard = Form(self.env['manage.task.complete'].with_context(
            active_model='manage.task', active_ids=drop.ids))
        wizard.mode = 'delete'
        wizard.save().action_confirm()
        self.assertFalse(drop.exists())

        # Open count only counts unfinished work; the sprint still counts archived work.
        self.project.invalidate_recordset()
        self.assertEqual(self.project.task_count, 1)
        other.action_done()
        self.project.invalidate_recordset()
        self.assertEqual(self.project.task_count, 0)
        self.assertEqual((self.sprint.item_count, self.sprint.done_points), (1, 2))
        self.assertEqual(self.sprint.progress, 100.0)

    def test_sprint_validation(self):
        with self.assertRaises(ValidationError):
            self.env['manage.sprint'].create({'project': self.project.id, 'duration': 0})

    # Dates, overdue ------------------------------------------------------

    def test_dates_and_pause(self):
        issue = self._issue()
        with self.assertRaises(ValidationError):
            issue.write({'start_date': self.now, 'end_date': self.now - timedelta(days=1)})
        with self.assertRaises(UserError):
            issue.action_toggle_pause()
        issue.write({'state': 'in_progress', 'is_paused': True})
        issue.state = 'done'
        self.assertFalse(issue.is_paused)

    def test_overdue(self):
        today = fields.Date.context_today(self.env.user)
        late = self._issue(date_deadline=today - timedelta(days=1))
        on_time = self._issue(date_deadline=today + timedelta(days=1))
        found = self.Issue.search([('is_overdue', '=', True)])
        self.assertIn(late, found)
        self.assertNotIn(on_time, found)

    # Migration -----------------------------------------------------------

    def test_migrate_old_bugs_and_improvements(self):
        old_bug = self.env['manage.bug'].create({
            'name': 'Old bug', 'history': self.history.id, 'state': 'review',
            'developer': [(6, 0, [self.dev.id])]})
        old_bug.message_post(body="a comment")
        self.env['manage.improvement'].create({'name': 'Old imp', 'history': self.history.id})
        migrate_to_issues(self.env)
        self.assertFalse(self.env['manage.bug'].search([]))
        self.assertFalse(self.env['manage.improvement'].search([]))
        bug = self.Issue.search([('name', '=', 'Old bug')])
        self.assertEqual(bug.issue_type, 'bug')
        self.assertEqual(bug.state, 'review')
        self.assertEqual(bug.stage_id.state, 'review')
        self.assertEqual(bug.assignee, self.dev)
        self.assertTrue(bug.key.startswith('WS-'))
        self.assertIn('a comment', ''.join(bug.message_ids.mapped('body')))
        self.assertEqual(self.Issue.search([('name', '=', 'Old imp')]).issue_type, 'improvement')

    # Developers ----------------------------------------------------------

    def test_existing_contact_becomes_developer_in_form(self):
        # Like the user's own contact: exists already, not a developer, no code.
        partner = self.env['res.partner'].create({'name': 'Me'})
        view = self.env.ref('manage.devs_partner_form')
        with Form(partner, view=view) as form:
            self.assertFalse(form._get_modifier('access_level', 'readonly'))
            form.is_dev = True
            form.access_level = '55556666c'
            # Still editable after typing, so the code is sent on save.
            self.assertFalse(form._get_modifier('access_level', 'readonly'))
        self.assertTrue(partner.is_dev)
        self.assertEqual(partner.access_level, '55556666C')
        with Form(partner, view=view) as form:
            self.assertTrue(form._get_modifier('access_level', 'readonly'), "locked once saved")

    def test_developer_code_and_category(self):
        self.assertEqual(self.dev.access_level, '11112222A')
        self.assertIn('Devs', self.dev.category_id.mapped('name'))
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self.env['res.partner'].create({
                    'name': 'Copy', 'is_dev': True, 'access_level': '11112222a'})
        with self.assertRaises(ValidationError):
            self.dev.access_level = '99998888B'
