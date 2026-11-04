# -*- coding: utf-8 -*-
from datetime import timedelta

from lxml import etree
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestDevProjects(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Task = cls.env['project.task']
        cls.project = cls.env['project.project'].create({'name': 'Web Shop'})
        cls.history = cls.env['dev.history'].create({'name': 'Login', 'project_id': cls.project.id})
        cls.sprint = cls.env['dev.sprint'].create({'name': 'S1', 'project_id': cls.project.id})
        cls.user = cls.env['res.users'].create({'name': 'Dev One', 'login': 'dev_one_test'})
        cls.user2 = cls.env['res.users'].create({'name': 'Dev Two', 'login': 'dev_two_test'})
        cls.stage_todo = cls.env.ref('dev_projects.stage_todo')
        cls.stage_progress = cls.env.ref('dev_projects.stage_in_progress')
        cls.stage_review = cls.env.ref('dev_projects.stage_review')
        cls.stage_done = cls.env.ref('dev_projects.stage_done')

    def _issue(self, **vals):
        return self.Task.create(dict({'name': 'T', 'project_id': self.project.id}, **vals))

    def _search_filter_domain(self, name):
        arch = self.Task.get_views([(self.env.ref('dev_projects.task_search').id, 'search')])['views']['search']['arch']
        node = etree.fromstring(arch).find(f".//filter[@name='{name}']")
        return safe_eval(node.get('domain'), {'uid': self.env.uid})

    # Projects and keys ------------------------------------------------------

    def test_project_defaults_and_keys(self):
        self.assertEqual(self.project.dev_key, 'WS')
        self.assertEqual(self.project.type_ids, self.stage_todo | self.stage_progress | self.stage_review | self.stage_done)
        a, b = self._issue(), self._issue()
        self.assertEqual((a.dev_key, b.dev_key), ('WS-1', 'WS-2'))
        self.assertEqual(a.display_name, '[WS-1] T')
        self.assertEqual(self.Task.search([('dev_key', '=', 'WS-2')]), b)
        self.assertIn(a.id, [r[0] for r in self.Task.name_search('WS-1')])
        other = self.env['project.project'].create({'name': 'Api', 'dev_key': 'api'})
        self.assertEqual(other.dev_key, 'API')
        a.project_id = other
        self.assertEqual(a.dev_key, 'API-1', "moving project gives a key from the new project")
        with self.assertRaises(UserError):
            self.project.dev_key = 'NEW'
        with self.assertRaises(ValidationError):
            self.env['project.project'].create({'name': 'Bad', 'dev_key': '1X'})

    # Board columns, status and the Project app's Done state ---------------

    def test_columns_and_project_state_stay_in_sync(self):
        issue = self._issue()
        self.assertEqual((issue.stage_id, issue.dev_status), (self.stage_todo, 'todo'))
        issue.stage_id = self.stage_progress  # kanban drag
        self.assertEqual(issue.dev_status, 'in_progress')
        self.assertTrue(issue.dev_start_date)
        issue.stage_id = self.stage_done
        self.assertEqual((issue.state, issue.dev_status), ('1_done', 'done'), "Done column = done in Project")
        self.assertTrue(issue.dev_end_date)
        issue.stage_id = self.stage_review
        self.assertEqual((issue.state, issue.dev_status), ('01_in_progress', 'review'), "moving out reopens it")
        self.assertFalse(issue.dev_end_date)
        # Marked done in the Project app (state checkbox): the card moves to Done.
        issue.state = '1_done'
        self.assertEqual(issue.stage_id, self.stage_done)
        # Reopened in the Project app: back to an In Progress column.
        issue.state = '01_in_progress'
        self.assertEqual((issue.stage_id, issue.dev_status), (self.stage_progress, 'in_progress'))

    def test_buttons(self):
        issue = self._issue()
        issue.action_dev_start()
        self.assertEqual(issue.stage_id, self.stage_progress)
        issue.action_dev_toggle_pause()
        self.assertTrue(issue.dev_is_paused)
        issue.action_dev_toggle_pause()
        issue.action_dev_review()
        self.assertEqual(issue.dev_status, 'review')
        issue.action_dev_done()
        self.assertEqual(issue.state, '1_done')
        issue.action_dev_reopen()
        self.assertEqual((issue.dev_status, issue.dev_end_date), ('todo', False))
        with self.assertRaises(UserError):
            issue.action_dev_toggle_pause()  # not in progress

    def test_wip_limit(self):
        self.stage_progress.dev_wip_limit = 1
        self._issue(dev_sprint_id=self.sprint.id, stage_id=self.stage_progress.id)
        second = self._issue(dev_sprint_id=self.sprint.id)
        with self.assertRaises(UserError):
            second.stage_id = self.stage_progress
        second.dev_sprint_id = False  # other sprint (backlog): its own count
        second.stage_id = self.stage_progress

    # People ---------------------------------------------------------------

    def test_assignee_and_project_assignees(self):
        issue = self._issue(dev_assignee_id=self.user.id)
        self.assertEqual(issue.dev_reporter_id, self.env.user)
        self.assertIn(self.user, issue.user_ids, "assignee is one of Project's assignees")
        issue.dev_assignee_id = self.user2
        self.assertTrue({self.user, self.user2} <= set(issue.user_ids))
        # Changed in the Project app: the Dev assignee follows.
        issue.user_ids = [(6, 0, [self.user.id])]
        self.assertEqual(issue.dev_assignee_id, self.user)
        from_project_app = self.Task.create({'name': 'P', 'project_id': self.project.id,
                                             'user_ids': [(6, 0, [self.user2.id])]})
        self.assertEqual(from_project_app.dev_assignee_id, self.user2)
        issue.with_user(self.user2).sudo().action_dev_assign_to_me()

    def test_priority_sync(self):
        issue = self._issue(dev_priority='3')
        self.assertEqual(issue.priority, '1', "Critical shows as starred in Project")
        issue.priority = '0'
        self.assertEqual(issue.dev_priority, '0')
        issue.priority = '1'
        self.assertEqual(issue.dev_priority, '2')

    # Sprints --------------------------------------------------------------

    def test_sprint_start_and_complete(self):
        nxt = self.env['dev.sprint'].create({'project_id': self.project.id})
        self.assertEqual(nxt.name, 'Sprint 2')
        done = self._issue(dev_sprint_id=self.sprint.id, dev_story_points=3)
        open_ = self._issue(dev_sprint_id=self.sprint.id, dev_story_points=5)
        backlog = self._issue()
        done.action_dev_done()
        self.assertFalse(backlog.dev_sprint_id, "new issues go to the backlog")

        self.sprint.action_start()
        self.assertEqual(self.sprint.state, 'running')
        with self.assertRaises(ValidationError):
            nxt.action_start()
        self.assertEqual(self.sprint.progress, 50.0)
        self.assertEqual((self.sprint.planned_points, self.sprint.done_points), (8, 3))
        self.assertEqual(self.sprint.end_date, self.sprint.start_date + timedelta(days=14))

        wizard = Form(self.env['dev.sprint.complete'].with_context(default_sprint_id=self.sprint.id))
        self.assertEqual((wizard.destination, wizard.target_sprint_id), ('sprint', nxt))
        wizard.save().action_confirm()
        self.assertEqual(self.sprint.state, 'closed')
        self.assertEqual(open_.dev_sprint_id, nxt)
        self.assertEqual(done.dev_sprint_id, self.sprint)
        with self.assertRaises(ValidationError):
            self.env['dev.sprint'].create({'project_id': self.project.id, 'duration': 0})

    def test_board(self):
        board = self.env.ref('dev_projects.action_board')
        ctx = safe_eval(board.context)
        self.assertEqual(ctx.get('search_default_dev_current_work'), 1)
        domain = safe_eval(board.domain) + self._search_filter_domain('dev_current_work')
        loose = self._issue()
        planned = self._issue(dev_sprint_id=self.sprint.id)
        self.assertIn(loose, self.Task.search(domain))
        self.assertNotIn(planned, self.Task.search(domain))
        self.sprint.action_start()
        created = self.Task.with_context(dev_board=True).create({'name': 'B', 'project_id': self.project.id})
        self.assertEqual(created.dev_sprint_id, self.sprint, "created on the board: running sprint")
        self.assertIn(planned, self.Task.search(domain))
        # Empty columns are shown on the board.
        groups = self.Task.with_context(dev_board=True, default_project_id=self.project.id).read_group(
            [('project_id', '=', self.project.id)], ['stage_id'], ['stage_id'])
        self.assertEqual(len(groups), 4)

    def test_complete_archive_and_delete(self):
        keep = self._issue(dev_story_points=2, dev_sprint_id=self.sprint.id)
        drop = self._issue()
        self.assertEqual(self.project.dev_open_issue_count, 2)
        action = keep.action_dev_open_complete_wizard()
        Form(self.env[action['res_model']].with_context(**action['context'])).save().action_confirm()
        self.assertEqual((keep.state, keep.active), ('1_done', False))
        self.assertIn(keep, self.Task.with_context(active_test=False).search(self._search_filter_domain('dev_archived')))
        wizard = Form(self.env['dev.task.complete'].with_context(active_model='project.task', active_ids=drop.ids))
        wizard.mode = 'delete'
        wizard.save().action_confirm()
        self.assertFalse(drop.exists())
        self.project.invalidate_recordset()
        self.assertEqual(self.project.dev_open_issue_count, 0)
        self.assertEqual((self.sprint.done_points, self.sprint.progress), (2, 100.0), "archived work still counts")

    # Checks ---------------------------------------------------------------

    def test_consistency_and_dates(self):
        other = self.env['project.project'].create({'name': 'Other'})
        with self.assertRaises(ValidationError):
            self._issue(project_id=other.id, dev_history_id=self.history.id)
        issue = self._issue(dev_history_id=self.history.id)
        self.assertEqual(self.history.task_count, 1)
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            issue.write({'dev_start_date': now, 'dev_end_date': now - timedelta(days=1)})
        issue.date_deadline = now - timedelta(days=1)
        self.assertTrue(issue.dev_is_overdue)
        self.assertIn(issue, self.Task.search([('dev_is_overdue', '=', True)]))

    # Developers -----------------------------------------------------------

    def test_developer_profile(self):
        partner = self.user.partner_id
        with Form(partner, view='dev_projects.developer_form') as form:
            form.dev_is_developer = True
            form.email = 'dev1@example.com'
            form.dev_access_code = '55556666c'
            self.assertFalse(form._get_modifier('dev_access_code', 'readonly'), "editable while typing")
        self.assertEqual(partner.dev_access_code, '55556666C')
        self.assertIn('Devs', partner.category_id.mapped('name'))
        with Form(partner, view='dev_projects.developer_form') as form:
            self.assertTrue(form._get_modifier('dev_access_code', 'readonly'), "locked once saved")
        with self.assertRaises(ValidationError):
            partner.dev_access_code = '11112222B'
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self.env['res.partner'].create({'name': 'Copy', 'dev_is_developer': True,
                                                'dev_access_code': '55556666c'})
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({'name': 'No code', 'dev_is_developer': True})
        self._issue(dev_assignee_id=self.user.id)
        partner.invalidate_recordset()
        self.assertEqual(partner.dev_open_issue_count, 1)

    def test_technology(self):
        tech = self.env['dev.technology'].create({'name': 'Zig Test'})
        issue = self._issue(dev_issue_type='bug', dev_technology_ids=[(6, 0, tech.ids)],
                            dev_history_id=self.history.id)
        self.assertEqual((tech.task_count, tech.bug_count), (1, 1))
        self.assertEqual(self.history.used_technology_ids, tech)
        self.assertEqual(issue.dev_severity, 'minor')
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self.env['dev.technology'].create({'name': 'Zig Test'})
