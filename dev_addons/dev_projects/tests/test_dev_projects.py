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
        cls.project = cls.env['project.project'].create({'name': 'Web Shop', 'dev_is_software': True})
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
        other = self.env['project.project'].create({'name': 'Api', 'dev_key': 'api', 'dev_is_software': True})
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
        # Done columns are never limited: finishing work must not be blocked.
        self.stage_done.dev_wip_limit = 1
        a, b = self._issue(), self._issue()
        a.action_dev_done()
        b.action_dev_done()
        self.assertEqual((a.dev_status, b.dev_status), ('done', 'done'))

    def test_board_issue_without_running_sprint_notifies(self):
        sent = []
        Bus = type(self.env['bus.bus'])
        self.patch(Bus, '_sendone', lambda bus, target, kind, payload: sent.append((target, kind, payload)))
        Board = self.Task.with_context(dev_board=True, default_project_id=self.project.id)
        issue = Board.create({'name': 'Lonely'})
        self.assertFalse(issue.dev_sprint_id, "no running sprint: it goes to the backlog")
        self.assertEqual(len(sent), 1)
        target, kind, payload = sent[0]
        self.assertEqual((target, kind), (self.env.user.partner_id, 'simple_notification'))
        self.assertIn('Lonely', payload['message'])
        self.sprint.action_start()
        self.assertEqual(Board.create({'name': 'In sprint'}).dev_sprint_id, self.sprint)
        self.assertEqual(len(sent), 1, "no note when the issue joins the running sprint")
        self._issue(name='Outside the board')
        self.assertEqual(len(sent), 1, "no note outside the board")

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

    def _board_ctx(self, xmlid='dev_projects.action_board', **extra):
        ctx = safe_eval(self.env.ref(xmlid).context)
        ctx = {k: v for k, v in ctx.items() if not k.startswith('search_default') and k != 'group_by'}
        return dict(ctx, **extra)

    def test_board_forms_use_running_sprint(self):
        """Every way of adding an issue from the board, the way the browser does it."""
        self.sprint.action_start()
        Board = self.Task.with_context(**self._board_ctx(default_project_id=self.project.id))
        form = Form(Board, view='project.view_task_form2')  # the "New" button
        self.assertEqual(form.dev_sprint_id, self.sprint, "shown in the form before saving")
        form.name = 'Full form'
        self.assertEqual(form.save().dev_sprint_id, self.sprint)
        quick = Form(Board, view='dev_projects.task_quick_create_form')
        quick.name = 'Quick'
        self.assertEqual(quick.save().dev_sprint_id, self.sprint)
        # Board from the menu (all projects): picking the project fills the sprint.
        form = Form(self.Task.with_context(**self._board_ctx()), view='project.view_task_form2')
        form.name = 'Menu board'
        form.project_id = self.project
        self.assertEqual(form.save().dev_sprint_id, self.sprint)
        # Emptying the Sprint field on purpose is respected.
        form = Form(Board, view='project.view_task_form2')
        form.name = 'Not now'
        form.dev_sprint_id = self.env['dev.sprint']
        self.assertFalse(form.save().dev_sprint_id)
        # The Backlog plans by hand: new rows start outside any sprint.
        for backlog_ctx in (self._board_ctx('dev_projects.action_backlog'),
                            self.project.action_dev_backlog()['context']):
            ctx = {k: v for k, v in backlog_ctx.items() if k != 'group_by'}
            row = Form(self.Task.with_context(**ctx), view='dev_projects.task_backlog_list')
            row.name = 'Backlog row'
            row.project_id = self.project
            self.assertFalse(row.save().dev_sprint_id)

    def test_board_form_without_running_sprint_notifies(self):
        sent = []
        self.patch(type(self.env['bus.bus']), '_sendone', lambda bus, *args: sent.append(args))
        form = Form(self.Task.with_context(**self._board_ctx(default_project_id=self.project.id)),
                    view='project.view_task_form2')
        form.name = 'Planned only'
        self.assertFalse(form.save().dev_sprint_id)
        self.assertEqual(len(sent), 1, "the full form also explains it went to the backlog")

    def test_complete_regular_task_returns_to_project_app(self):
        regular = self.env['project.project'].create({'name': 'Office'})
        task = self.Task.create({'name': 'Chairs', 'project_id': regular.id})
        wizard = self.env['dev.task.complete'].with_context(active_model='project.task', active_ids=task.ids).create({})
        action = wizard.action_confirm()
        self.assertEqual(action['res_model'], 'project.task')
        self.assertNotIn('dev_board', str(action.get('context')), "stays in the Project app")
        self.assertFalse(task.active)

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

    def test_move_and_duplicate_leave_sprint_behind(self):
        issue = self._issue(dev_sprint_id=self.sprint.id, dev_history_id=self.history.id)
        # Duplicating the project copies the issue without the old sprint/history.
        copy = self.project.copy()
        copied = copy.with_context(active_test=False).task_ids
        self.assertEqual(len(copied), 1)
        self.assertFalse(copied.dev_sprint_id or copied.dev_history_id)
        self.assertTrue(copied.dev_key.startswith(copy.dev_key + '-'))
        # Duplicating the issue in the same project keeps them.
        same = issue.copy()
        self.assertEqual((same.dev_sprint_id, same.dev_history_id), (self.sprint, self.history))
        # Moving to another project from a list or mass edit (no onchange).
        other = self.env['project.project'].create({'name': 'Mobile', 'dev_is_software': True})
        issue.write({'project_id': other.id})
        self.assertFalse(issue.dev_sprint_id or issue.dev_history_id)
        self.assertTrue(issue.dev_key.startswith('MOB'))
        # Picking a sprint of the new project in the same write keeps it.
        target = self.env['dev.sprint'].create({'project_id': self.project.id})
        issue.write({'project_id': self.project.id, 'dev_sprint_id': target.id})
        self.assertEqual(issue.dev_sprint_id, target)

    def test_portal_user_of_shared_project(self):
        self.project.privacy_visibility = 'portal'
        portal = self.env['res.users'].create({
            'name': 'Customer', 'login': 'dev_portal_test', 'email': 'customer@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])]})
        self.project.message_subscribe(partner_ids=portal.partner_id.ids)
        self.project.write({'collaborator_ids': [(0, 0, {'partner_id': portal.partner_id.id})]})
        issue = self._issue()
        as_portal = issue.with_user(portal)
        as_portal.write({'stage_id': self.stage_progress.id})
        self.assertEqual(issue.dev_status, 'in_progress')
        self.assertTrue(issue.dev_start_date)
        as_portal.write({'state': '1_done'})
        self.assertEqual((issue.stage_id, issue.dev_status), (self.stage_done, 'done'))
        self.assertTrue(issue.dev_end_date)

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

    # Software vs regular projects --------------------------------------------

    def test_regular_projects_stay_plain(self):
        """Other teams' projects behave exactly like the plain Project app."""
        regular = self.env['project.project'].create({'name': 'Marketing'})
        self.assertFalse(regular.dev_is_software)
        self.assertFalse(regular.dev_key, "no key for regular projects")
        self.assertFalse(regular.type_ids, "no Dev board columns forced on them")
        done_like = self.env['project.task.type'].create({
            'name': 'Done', 'dev_category': 'done', 'project_ids': [(4, regular.id)]})
        task = self.Task.create({'name': 'Flyer', 'project_id': regular.id})
        self.assertFalse(task.dev_key)
        self.assertEqual(task.display_name, 'Flyer')
        task.stage_id = done_like
        self.assertEqual(task.state, '01_in_progress', "Project's own rule: a stage does not close a task")
        task.user_ids = [(6, 0, [self.user.id])]
        self.assertFalse(task.dev_assignee_id)

        # Dev Projects screens do not list it.
        board = self.env.ref('dev_projects.action_board')
        self.assertNotIn(task, self.Task.search(safe_eval(board.domain)))
        dev_projects = self.env.ref('dev_projects.action_project')
        self.assertNotIn(regular, self.env['project.project'].search(safe_eval(dev_projects.domain)))

        # Ticking "Software Project" later moves it over: key, numbered tasks.
        regular.dev_is_software = True
        self.assertEqual(regular.dev_key, 'MARK')
        self.assertEqual(task.dev_key, 'MARK-1')
        self.assertIn(task, self.Task.search(safe_eval(board.domain)))

    def test_project_app_hides_software_by_default(self):
        regular = self.env['project.project'].create({'name': 'Sales Ops'})
        Project = self.env['project.project']
        arch = Project.get_views([(self.env.ref('project.view_project_project_filter').id, 'search')])['views']['search']['arch']
        hide = safe_eval(etree.fromstring(arch).find(".//filter[@name='dev_hide_software']").get('domain'))
        found = Project.search(hide)
        self.assertIn(regular, found)
        self.assertNotIn(self.project, found)
        task_soft = self._issue()
        task_regular = self.Task.create({'name': 'R', 'project_id': regular.id})
        private = self.Task.create({'name': 'Private', 'user_ids': [(6, 0, [self.env.uid])]})
        task_arch = self.Task.get_views([(self.env.ref('project.view_task_search_form').id, 'search')])['views']['search']['arch']
        task_hide = safe_eval(etree.fromstring(task_arch).find(".//filter[@name='dev_hide_software']").get('domain'))
        tasks = self.Task.search(task_hide)
        self.assertIn(task_regular, tasks)
        self.assertIn(private, tasks)
        self.assertNotIn(task_soft, tasks)
        # On by default in the Project menus, and removable (it is a filter, not a hard rule).
        for xmlid in ('project.open_view_project_all', 'project.action_view_all_task',
                      'project.action_view_my_task', 'project.action_project_task_user_tree'):
            ctx = safe_eval(self.env.ref(xmlid).context, {'uid': self.env.uid})
            self.assertEqual(ctx.get('search_default_dev_hide_software'), 1, xmlid)
        self.assertIn(self.project, Project.search([]), "managers can still see everything")
