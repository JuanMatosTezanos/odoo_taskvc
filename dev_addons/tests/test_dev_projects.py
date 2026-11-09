# -*- coding: utf-8 -*-
from datetime import timedelta

from lxml import etree
from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
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
        cls.milestone = cls.env['project.milestone'].create({'name': 'Login', 'project_id': cls.project.id})
        cls.sprint = cls.env['dev.sprint'].create({'name': 'S1', 'project_id': cls.project.id})
        cls.user = cls.env['res.users'].create({'name': 'Dev One', 'login': 'dev_one_test'})
        cls.user2 = cls.env['res.users'].create({'name': 'Dev Two', 'login': 'dev_two_test'})
        cls.stage_todo = cls.env.ref('dev_addons.stage_todo')
        cls.stage_progress = cls.env.ref('dev_addons.stage_in_progress')
        cls.stage_review = cls.env.ref('dev_addons.stage_review')
        cls.stage_done = cls.env.ref('dev_addons.stage_done')

    def _issue(self, **vals):
        return self.Task.create(dict({'name': 'T', 'project_id': self.project.id}, **vals))

    def _search_filter_domain(self, name):
        arch = self.Task.get_views([(self.env.ref('dev_addons.task_search').id, 'search')])['views']['search']['arch']
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

    def test_sprint_buttons_refresh_project_form(self):
        """From the project's Sprints tab, Start/Complete reload the project so
        "Running Sprint" is up to date; from the Sprints menu nothing changes."""
        from_menu = self.env['dev.sprint'].create({'project_id': self.project.id})
        self.assertFalse(from_menu.action_start(), "Sprints menu: stay on the sprint")
        action = from_menu.action_open_complete_wizard()
        wizard = Form(self.env['dev.sprint.complete'].with_context(**action['context'])).save()
        wizard.destination = 'backlog'
        recap = wizard.action_confirm()
        self.assertEqual((recap['res_model'], recap['res_id'], recap['target']), ('dev.sprint', from_menu.id, 'new'))
        self.assertEqual(from_menu.with_context(**recap['context']).action_dev_recap_done()['type'],
                         'ir.actions.act_window_close')
        from_tab = self.sprint.with_context(dev_reload_project=True)
        self.assertEqual(from_tab.action_start()['tag'], 'soft_reload')
        self.assertEqual(self.project.dev_running_sprint_id, self.sprint)
        action = from_tab.action_open_complete_wizard()
        wizard = Form(self.env['dev.sprint.complete'].with_context(**action['context'])).save()
        wizard.destination = 'backlog'
        recap = wizard.action_confirm()
        self.assertEqual(recap['res_id'], self.sprint.id)
        self.assertEqual(self.sprint.with_context(**recap['context']).action_dev_recap_done()['tag'], 'soft_reload',
                         "Save in the recap reloads the project")
        self.assertFalse(self.project.dev_running_sprint_id)

    def test_board(self):
        board = self.env.ref('dev_addons.action_board')
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

    def _board_ctx(self, xmlid='dev_addons.action_board', **extra):
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
        quick = Form(Board, view='dev_addons.task_quick_create_form')
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
        for backlog_ctx in (self._board_ctx('dev_addons.action_backlog'),
                            self.project.action_dev_backlog()['context']):
            ctx = {k: v for k, v in backlog_ctx.items() if k != 'group_by'}
            row = Form(self.Task.with_context(**ctx), view='dev_addons.task_backlog_list')
            row.name = 'Backlog row'
            row.project_id = self.project
            self.assertFalse(row.save().dev_sprint_id)

    def test_backlog_rows_can_be_opened(self):
        # Rows edit in place, so each one needs a "View" button to open the full issue.
        arch = self.env.ref('dev_addons.task_backlog_list').arch
        self.assertIn('open_form_view="1"', arch)
        views = self.env.ref('dev_addons.action_backlog').view_ids.mapped('view_mode')
        self.assertIn('form', views)

    def test_severity_is_editable(self):
        # Both the issue form and a Backlog row let you pick a bug's severity.
        bug = self._issue(dev_issue_type='bug')
        with Form(bug) as form:
            form.dev_severity = 'critical'
        self.assertEqual(bug.dev_severity, 'critical')
        row = Form(self.Task.with_context(dev_backlog=True), view='dev_addons.task_backlog_list')
        row.name = 'Bug from the backlog'
        row.project_id = self.project
        row.dev_issue_type = 'bug'
        row.dev_severity = 'blocker'
        self.assertEqual(row.save().dev_severity, 'blocker')

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

    # Milestones -------------------------------------------------------------

    def test_software_project_setup(self):
        """Software projects: milestones on, tasks called Issues, a repository link."""
        self.assertTrue(self.project.allow_milestones)
        self.assertEqual(self.project.label_tasks, 'Issues')
        self.assertTrue(self.env.user.has_group('project.group_project_milestone'))
        self.project.dev_repository_url = 'https://github.com/company/web-shop'
        regular = self.env['project.project'].create({'name': 'Picnic', 'label_tasks': 'Chores'})
        self.assertEqual(regular.label_tasks, 'Chores', "regular projects keep their own label")
        regular.dev_is_software = True
        self.assertEqual((regular.label_tasks, regular.allow_milestones), ('Issues', True))
        # The form hides "Name of the Tasks" and Tags on software projects only.
        with Form(self.project) as form:
            self.assertTrue(form._get_modifier('label_tasks', 'invisible'))
            self.assertTrue(form._get_modifier('tag_ids', 'invisible'))
        with Form(self.env['project.project'].create({'name': 'Garden'})) as form:
            self.assertFalse(form._get_modifier('label_tasks', 'invisible'))
            self.assertFalse(form._get_modifier('tag_ids', 'invisible'))

    def test_sprint_issues_join_its_milestone(self):
        self.sprint.milestone_id = self.milestone
        # Created in the sprint (code, quick create, the sprint's issue list, the form).
        a = self._issue(dev_sprint_id=self.sprint.id)
        self.assertEqual(a.milestone_id, self.milestone)
        form = Form(self.Task.with_context(default_project_id=self.project.id, default_dev_sprint_id=self.sprint.id),
                    view='project.view_task_form2')
        self.assertEqual(form.milestone_id, self.milestone, "shown in the form before saving")
        form.name = 'From the sprint'
        self.assertEqual(form.save().milestone_id, self.milestone)
        # Planned into the sprint later (backlog), or picked in the form.
        b = self._issue()
        b.dev_sprint_id = self.sprint
        self.assertEqual(b.milestone_id, self.milestone)
        form = Form(self._issue(), view='project.view_task_form2')
        form.dev_sprint_id = self.sprint
        self.assertEqual(form.milestone_id, self.milestone)
        # An issue that already has a milestone keeps it.
        other_goal = self.env['project.milestone'].create({'name': 'Payments', 'project_id': self.project.id})
        c = self._issue(milestone_id=other_goal.id)
        c.dev_sprint_id = self.sprint
        self.assertEqual(c.milestone_id, other_goal)
        # Linking a sprint to a milestone later fills its issues without one.
        later = self.env['dev.sprint'].create({'project_id': self.project.id})
        d = self._issue(dev_sprint_id=later.id)
        later.milestone_id = other_goal
        self.assertEqual(d.milestone_id, other_goal)
        self.assertEqual(self.milestone.dev_sprint_ids, self.sprint)

    def test_milestone_progress_and_complete(self):
        self.sprint.milestone_id = self.milestone
        done = self._issue(milestone_id=self.milestone.id, dev_story_points=3, dev_issue_type='bug')
        self._issue(milestone_id=self.milestone.id, dev_story_points=5)
        done.action_dev_done()
        m = self.milestone
        self.assertEqual((m.dev_issue_count, m.dev_done_count, m.dev_open_count), (2, 1, 1))
        self.assertEqual((m.dev_planned_points, m.dev_done_points, m.dev_bug_count), (8, 3, 1))
        self.assertEqual((m.dev_progress, m.dev_sprint_count), (50.0, 1))
        # Completed (archived) issues still count as done work.
        action = done.action_dev_open_complete_wizard()
        Form(self.env[action['res_model']].with_context(**action['context'])).save().action_confirm()
        m.invalidate_recordset()
        self.assertEqual((m.dev_issue_count, m.dev_done_count), (2, 1))
        m.action_dev_complete()
        self.assertTrue(m.is_reached)
        self.assertTrue(m.reached_date)
        m.action_dev_reopen()
        self.assertFalse(m.is_reached)
        # Its buttons open the board and the sprints, filtered on it.
        board = m.action_dev_view_issues()
        self.assertEqual(self.Task.search(board['domain']), m.task_ids)
        self.assertEqual(board['context']['default_milestone_id'], m.id)
        sprints = m.action_dev_view_sprints()
        self.assertEqual(self.env['dev.sprint'].search(sprints['domain']), self.sprint)

    def test_milestone_links_existing_sprints(self):
        """From a milestone's Sprints tab, "Add" links a sprint that already exists."""
        issue = self._issue(dev_sprint_id=self.sprint.id)
        # What the screen sends when you pick a sprint in the list ("Add").
        self.milestone.write({'dev_sprint_ids': [Command.link(self.sprint.id)]})
        self.assertEqual(self.sprint.milestone_id, self.milestone)
        self.assertEqual(issue.milestone_id, self.milestone, "the sprint's issues join the milestone")
        # Removing the line unlinks the sprint; the sprint itself stays.
        self.milestone.write({'dev_sprint_ids': [Command.unlink(self.sprint.id)]})
        self.assertTrue(self.sprint.exists())
        self.assertFalse(self.sprint.milestone_id)
        # The tab uses the "pick existing" widget, limited to this project's open sprints.
        arch = self.env['project.milestone'].get_views(
            [(self.env.ref('dev_addons.milestone_form').id, 'form')])['views']['form']['arch']
        field = etree.fromstring(arch).find(".//field[@name='dev_sprint_ids']")
        self.assertEqual(field.get('widget'), 'many2many')

    def test_milestone_forms(self):
        with Form(self.env['project.milestone'].with_context(default_project_id=self.project.id),
                  view='dev_addons.milestone_form') as form:
            form.name = 'Beta launch'
            form.deadline = fields.Date.today() - timedelta(days=1)
        milestone = form.record
        self.assertTrue(milestone.is_deadline_exceeded, "late: shown in red with a Late ribbon")
        with Form(self.env['dev.sprint']) as form:
            form.project_id = self.project
            form.milestone_id = milestone
        self.assertEqual(form.record.milestone_id, milestone)
        # The project form's Milestones tab.
        with Form(self.project) as form:
            with form.milestone_ids.new() as line:
                line.name = 'From the project tab'
        self.assertIn('From the project tab', self.project.milestone_ids.mapped('name'))

    def test_milestone_version(self):
        for version in ('1.0', '1.2.0', 'v2.0.1', 'V3', '2.1.0-beta', '10.4.2.1'):
            self.milestone.dev_version = version
            self.assertEqual(self.milestone.dev_version, version)
        self.milestone.dev_version = '  1.3.0 '
        self.assertEqual(self.milestone.dev_version, '1.3.0', "spaces are trimmed")
        for bad in ('beta', 'version 1', '1..2', '1.2.', 'v', '1.2.3.4.5', '1,2'):
            with self.assertRaises(ValidationError, msg=bad):
                self.milestone.dev_version = bad
        self.milestone.dev_version = False
        with Form(self.env['project.milestone'].with_context(default_project_id=self.project.id),
                  view='dev_addons.milestone_form') as form:
            form.name = 'Release'
            form.dev_version = '2.0.0'
        self.assertEqual(form.record.dev_version, '2.0.0')

    # Sub-tasks --------------------------------------------------------------

    def test_subtasks_live_inside_their_parent(self):
        login = self.env['dev.module'].create({'name': 'Login', 'project_id': self.project.id})
        parent = self._issue(dev_sprint_id=self.sprint.id, dev_module_id=login.id, dev_story_points=5)
        # Added in the parent's Sub-tasks tab.
        with Form(parent, view='project.view_task_form2') as form:
            with form.child_ids.new() as line:
                line.name = 'Write the API'
        sub = parent.child_ids
        self.assertEqual(len(sub), 1)
        self.assertFalse(sub.display_in_project, "shown inside the parent, not on the board")
        self.assertTrue(sub.dev_key.startswith('WS-'), "sub-tasks get their own key")
        self.assertEqual((sub.dev_sprint_id, sub.dev_module_id), (self.sprint, login))
        # Created from code, even from the board: still the parent's sprint.
        sub2 = self.Task.with_context(dev_board=True).create({'name': 'Tests', 'parent_id': parent.id})
        self.assertEqual((sub2.project_id, sub2.dev_sprint_id), (self.project, self.sprint))
        self.assertFalse(sub2.display_in_project)
        # They don't count on their own: their parent does.
        self.assertEqual(self.sprint.item_count, 1)
        self.assertEqual(self.sprint.planned_points, 5)
        self.assertEqual(login.issue_count, 1)
        self.assertEqual(self.project.dev_open_issue_count, 1)
        self.assertNotIn(sub, self.Task.search(self.project.action_dev_board()['domain']))
        self.assertNotIn(sub, self.Task.search(safe_eval(self.env.ref('dev_addons.action_board').domain)))
        self.assertIn(parent, self.Task.search(self.project.action_dev_backlog()['domain']))
        self.assertNotIn(sub, self.Task.search(self.project.action_dev_backlog()['domain']))
        self.assertEqual((parent.subtask_count, parent.closed_subtask_count), (2, 0))
        sub.action_dev_done()
        parent.invalidate_recordset(['closed_subtask_count'])
        self.assertEqual(parent.closed_subtask_count, 1)
        # The parent moves to another sprint: its sub-tasks follow.
        nxt = self.env['dev.sprint'].create({'project_id': self.project.id})
        parent.dev_sprint_id = nxt
        self.assertEqual((sub | sub2).dev_sprint_id, nxt)
        # Its component changes: sub-tasks with the same (or none) follow, others keep theirs.
        camera = self.env['dev.module'].create({'name': 'Camera', 'project_id': self.project.id})
        other = self.env['dev.module'].create({'name': 'Other', 'project_id': self.project.id})
        sub2.dev_module_id = other
        parent.dev_module_id = camera
        self.assertEqual((sub.dev_module_id, sub2.dev_module_id), (camera, other))
        # A task made a sub-task later joins its parent's sprint.
        loose = self._issue()
        loose.write({'parent_id': parent.id, 'display_in_project': False})
        self.assertEqual(loose.dev_sprint_id, nxt)

    def test_subtasks_and_wip_limit(self):
        """Sub-tasks are not cards on the board, so they don't fill a column's WIP limit."""
        self.stage_progress.dev_wip_limit = 1
        parent = self._issue(dev_sprint_id=self.sprint.id, stage_id=self.stage_progress.id)
        sub = self.Task.create({'name': 'Sub', 'parent_id': parent.id})
        sub.stage_id = self.stage_progress
        self.assertEqual(sub.dev_status, 'in_progress')

    def test_subtasks_move_with_parent_when_sprint_completes(self):
        parent = self._issue(dev_sprint_id=self.sprint.id)
        sub = self.Task.create({'name': 'Sub', 'parent_id': parent.id})
        nxt = self.env['dev.sprint'].create({'project_id': self.project.id})
        self.sprint.action_start()
        wizard = Form(self.env['dev.sprint.complete'].with_context(default_sprint_id=self.sprint.id)).save()
        self.assertEqual((wizard.done_count, wizard.open_count), (0, 1))
        wizard.action_confirm()
        self.assertEqual((parent.dev_sprint_id, sub.dev_sprint_id), (nxt, nxt))

    def test_issue_form_for_subtasks(self):
        arch = self.Task.get_views([(self.env.ref('project.view_task_form2').id, 'form')])['views']['form']['arch']
        doc = etree.fromstring(arch)
        sprint = doc.find(".//field[@name='dev_sprint_id']")
        self.assertIn('parent_id and not display_in_project', sprint.get('readonly'), "sprint follows the parent")
        points = doc.find(".//field[@name='dev_story_points']")
        self.assertIn('parent_id and not display_in_project', points.get('invisible'))
        self.assertIsNotNone(doc.find(".//field[@name='child_ids']/tree/field[@name='dev_key']"))
        # One Assignee on software issues: Odoo's Assignees field is hidden there.
        self.assertEqual(doc.find(".//field[@name='user_ids']").get('invisible'), 'dev_project_is_software')

    # Sprint recap -----------------------------------------------------------

    def test_sprint_recap(self):
        login = self.env['dev.module'].create({'name': 'Login', 'project_id': self.project.id})
        story = self._issue(dev_sprint_id=self.sprint.id, dev_issue_type='story', dev_story_points=5,
                            dev_module_id=login.id, dev_assignee_id=self.user.id)
        bug = self._issue(dev_sprint_id=self.sprint.id, dev_issue_type='bug', dev_story_points=2,
                          dev_assignee_id=self.user2.id)
        bug2 = self._issue(dev_sprint_id=self.sprint.id, dev_issue_type='bug', dev_story_points=1,
                           dev_module_id=login.id, dev_assignee_id=self.user.id)
        unfinished = self._issue(dev_sprint_id=self.sprint.id, dev_story_points=8)
        sub = self.Task.create({'name': 'Sub', 'parent_id': story.id})
        (story | bug | bug2 | sub).action_dev_done()
        # A finished issue completed and archived still shows in the recap.
        action = bug2.action_dev_open_complete_wizard()
        Form(self.env[action['res_model']].with_context(**action['context'])).save().action_confirm()
        nxt = self.env['dev.sprint'].create({'project_id': self.project.id})
        self.sprint.action_start()
        recap = Form(self.env['dev.sprint.complete'].with_context(default_sprint_id=self.sprint.id)).save().action_confirm()
        self.assertEqual((recap['res_model'], recap['res_id'], recap['target']), ('dev.sprint', self.sprint.id, 'new'))
        self.assertEqual(recap['views'][0][0], self.env.ref('dev_addons.sprint_recap_form').id)

        s = self.sprint
        self.assertEqual((s.recap_issue_count, s.recap_done_count, s.recap_progress), (4, 3, 75.0),
                         "sub-tasks count inside their parent")
        self.assertEqual((s.recap_planned_points, s.recap_done_points), (16, 8))
        self.assertEqual((s.recap_moved_count, s.recap_moved_sprint_id, s.recap_moved_to), (1, nxt, nxt.name))
        self.assertEqual(s.recap_done_task_ids, story | bug | bug2)
        self.assertEqual(s.recap_moved_task_ids, unfinished)
        by_type = {line.name: (line.issue_count, line.points) for line in s.recap_type_line_ids}
        self.assertEqual(by_type, {'Story': (1, 5), 'Bug': (2, 3)})
        by_component = {line.name: (line.issue_count, line.points) for line in s.recap_component_line_ids}
        self.assertEqual(by_component, {'Login': (2, 6), 'No component': (1, 2)})
        by_person = {line.name: (line.issue_count, line.points) for line in s.recap_person_line_ids}
        self.assertEqual(by_person, {'Dev One': (2, 6), 'Dev Two': (1, 2)})
        # The recap stays as it was, even after its issues change.
        unfinished.action_dev_done()
        self.assertEqual(s.recap_done_count, 3)
        # The team writes its summary in the pop-up, and Save closes it.
        with Form(s, view='dev_addons.sprint_recap_form') as form:
            form.recap_notes = '<p>Login is done.</p>'
        self.assertIn('Login is done.', s.recap_notes)
        self.assertEqual(s.action_dev_recap_done()['type'], 'ir.actions.act_window_close')
        # The sprint form opens on a Recap tab once the sprint is closed.
        arch = self.env['dev.sprint'].get_views([(False, 'form')])['views']['form']['arch']
        first_page = etree.fromstring(arch).find('.//notebook/page')
        self.assertEqual((first_page.get('name'), first_page.get('invisible')), ('recap', "state != 'closed'"))
        Form(s)  # opens

    def test_sprint_recap_everything_to_backlog(self):
        issue = self._issue(dev_sprint_id=self.sprint.id)
        self.sprint.action_start()
        wizard = Form(self.env['dev.sprint.complete'].with_context(default_sprint_id=self.sprint.id)).save()
        wizard.destination = 'backlog'
        wizard.action_confirm()
        s = self.sprint
        self.assertEqual((s.recap_done_count, s.recap_moved_count, s.recap_moved_to), (0, 1, 'Backlog'))
        self.assertFalse(issue.dev_sprint_id)
        self.assertFalse(s.recap_line_ids)

    # Components (technical name: dev.module) --------------------------------

    def test_modules(self):
        Module = self.env['dev.module']
        login = Module.create({'name': 'Login', 'project_id': self.project.id, 'lead_id': self.user.id})
        bug = self._issue(dev_module_id=login.id, dev_issue_type='bug')
        done = self._issue(dev_module_id=login.id)
        done.action_dev_done()
        self.assertEqual((login.issue_count, login.open_count, login.bug_count), (2, 1, 1))
        self.assertEqual(self.Task.search(login.action_view_issues()['domain']), bug | done)
        # Shown on the issue form; a new name can be created right there.
        form = Form(self.Task.with_context(default_project_id=self.project.id), view='project.view_task_form2')
        form.name = 'Camera crash'
        module_id, _name = Module.with_context(default_project_id=self.project.id).name_create('Camera')
        form.dev_module_id = Module.browse(module_id)
        issue = form.save()
        self.assertEqual((issue.dev_module_id.name, issue.dev_module_id.project_id), ('Camera', self.project))
        # Same name twice in one project is refused; another project may reuse it.
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                Module.create({'name': 'Login', 'project_id': self.project.id})
        other = self.env['project.project'].create({'name': 'Mobile', 'dev_is_software': True})
        Module.create({'name': 'Login', 'project_id': other.id})
        # A module of another project is refused, and moving the issue drops it.
        with self.assertRaises(ValidationError):
            self._issue(project_id=other.id, dev_module_id=login.id)
        bug.write({'project_id': other.id})
        self.assertFalse(bug.dev_module_id)

    def test_project_modules_tab(self):
        with Form(self.project) as form:
            with form.dev_module_ids.new() as line:
                line.name = 'UI'
        self.assertEqual(self.project.dev_module_ids.mapped('name'), ['UI'])
        # Odoo's "Tasks" button is hidden on software projects ("Open Issues" replaces it).
        arch = self.env['project.project'].get_views([(False, 'form')])['views']['form']['arch']
        button = etree.fromstring(arch).find(".//button[@name='action_view_tasks']")
        self.assertEqual(button.get('invisible'), 'dev_is_software')

    def test_delete_project_with_status_updates(self):
        """A project with status updates can be deleted in one go (regular or software)."""
        for vals in ({'name': 'Old Software', 'dev_is_software': True}, {'name': 'Old Office'}):
            project = self.env['project.project'].create(vals)
            updates = self.env['project.update'].create([
                {'name': f'Week {n}', 'project_id': project.id, 'status': 'on_track'} for n in range(1, 4)])
            self.Task.create({'name': 'Leftover', 'project_id': project.id})
            project.unlink()
            self.assertFalse(project.exists())
            self.assertFalse(updates.exists(), "its updates are deleted with it")
        # Still only for people allowed to delete projects.
        project = self.env['project.project'].create({'name': 'Kept'})
        update = self.env['project.update'].create({'name': 'Note', 'project_id': project.id, 'status': 'on_track'})
        viewer = self.env['res.users'].create({'name': 'Viewer', 'login': 'viewer_dev_test',
                                               'groups_id': [Command.set([self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            project.with_user(viewer).unlink()
        self.assertTrue(update.exists(), "nothing is deleted when the project can't be")

    def test_duplicate_project_copies_modules(self):
        login = self.env['dev.module'].create({'name': 'Login', 'project_id': self.project.id})
        self._issue(dev_module_id=login.id)
        copy = self.project.copy()
        self.assertEqual(copy.dev_module_ids.mapped('name'), ['Login'])
        copied = copy.with_context(active_test=False).task_ids
        self.assertEqual(copied.dev_module_id, copy.dev_module_ids, "points to the copied module")
        self.assertEqual(login.issue_count, 1, "the original keeps its issue")

    # Checks ---------------------------------------------------------------

    def test_consistency_and_dates(self):
        other = self.env['project.project'].create({'name': 'Other', 'dev_is_software': True})
        with self.assertRaises(ValidationError):
            self._issue(project_id=other.id, milestone_id=self.milestone.id)
        with self.assertRaises(ValidationError):
            self.env['dev.sprint'].create({'project_id': other.id, 'milestone_id': self.milestone.id})
        issue = self._issue(milestone_id=self.milestone.id)
        self.assertEqual(self.milestone.dev_issue_count, 1)
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            issue.write({'dev_start_date': now, 'dev_end_date': now - timedelta(days=1)})
        issue.date_deadline = now - timedelta(days=1)
        self.assertTrue(issue.dev_is_overdue)
        self.assertIn(issue, self.Task.search([('dev_is_overdue', '=', True)]))

    def test_move_and_duplicate_leave_sprint_behind(self):
        issue = self._issue(dev_sprint_id=self.sprint.id, milestone_id=self.milestone.id)
        # Duplicating the project copies the milestones too (Odoo does that) and
        # points the copied issue to the copied milestone; the sprint stays behind.
        copy = self.project.copy()
        copied = copy.with_context(active_test=False).task_ids
        self.assertEqual(len(copied), 1)
        self.assertFalse(copied.dev_sprint_id)
        self.assertEqual(copied.milestone_id.project_id, copy)
        self.assertEqual(copied.milestone_id.name, 'Login')
        self.assertTrue(copied.dev_key.startswith(copy.dev_key + '-'))
        # Duplicating the issue in the same project keeps them.
        same = issue.copy()
        self.assertEqual((same.dev_sprint_id, same.milestone_id), (self.sprint, self.milestone))
        # Duplicating it into another project drops them.
        other = self.env['project.project'].create({'name': 'Mobile', 'dev_is_software': True})
        elsewhere = issue.copy({'project_id': other.id})
        self.assertFalse(elsewhere.dev_sprint_id or elsewhere.milestone_id)
        # Moving to another project from a list or mass edit (no onchange).
        issue.write({'project_id': other.id})
        self.assertFalse(issue.dev_sprint_id or issue.milestone_id)
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
        with Form(partner, view='dev_addons.developer_form') as form:
            form.dev_is_developer = True
            form.email = 'dev1@example.com'
            form.dev_access_code = '55556666c'
            self.assertFalse(form._get_modifier('dev_access_code', 'readonly'), "editable while typing")
        self.assertEqual(partner.dev_access_code, '55556666C')
        self.assertIn('Devs', partner.category_id.mapped('name'))
        with Form(partner, view='dev_addons.developer_form') as form:
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

    def test_developer_create_user(self):
        dev = self.env['res.partner'].create({'name': 'Wil Test', 'dev_is_developer': True,
                                              'dev_access_code': '87654321K'})
        with self.assertRaises(UserError):
            dev.action_dev_create_user()  # no email yet
        dev.email = 'wil.test@example.com'
        dev.with_context(no_reset_password=True).action_dev_create_user()
        user = dev.user_ids
        self.assertEqual(len(user), 1)
        self.assertEqual(user.partner_id, dev, "same contact: the profile stays on it")
        self.assertEqual(dev.dev_access_code, '87654321K')
        self.assertEqual(user.login, 'wil.test@example.com')
        self.assertFalse(user.share, "internal user, so it can be an assignee")
        self.assertTrue(user.has_group('project.group_project_user'))
        self.assertEqual(self.env['res.partner'].search_count([('name', '=', 'Wil Test')]), 1, "no duplicate contact")
        # Now assignable from an issue form, and counted on the developer.
        form = Form(self.Task.with_context(default_project_id=self.project.id), view='project.view_task_form2')
        form.name = 'For Wil'
        form.dev_assignee_id = user
        issue = form.save()
        self.assertIn(user, issue.user_ids)
        dev.invalidate_recordset()
        self.assertEqual(dev.dev_open_issue_count, 1)
        # He can open his issues, and the button refuses a second user.
        self.assertEqual(self.Task.search(dev.action_dev_view_issues()['domain']), issue)
        with self.assertRaises(UserError):
            dev.action_dev_create_user()

    def test_technology(self):
        tech = self.env['dev.technology'].create({'name': 'Zig Test'})
        issue = self._issue(dev_issue_type='bug', dev_technology_ids=[(6, 0, tech.ids)],
                            milestone_id=self.milestone.id)
        self.assertEqual((tech.task_count, tech.bug_count), (1, 1))
        self.assertEqual(self.milestone.dev_technology_ids, tech)
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
        board = self.env.ref('dev_addons.action_board')
        self.assertNotIn(task, self.Task.search(safe_eval(board.domain)))
        dev_action = self.env.ref('dev_addons.action_project')
        self.assertNotIn(regular, self.env['project.project'].search(safe_eval(dev_action.domain)))

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

    # Spanish ----------------------------------------------------------------

    def test_spanish_translation(self):
        """With Spanish installed (any variant, e.g. Dominican Republic), each
        user who picks it in their Preferences sees Dev Projects in Spanish."""
        self.env['res.lang']._activate_lang('es_DO')
        self.env['ir.module.module']._load_module_terms(['dev_addons'], ['es_DO'])
        env = self.env(context=dict(self.env.context, lang='es_DO'))
        self.assertEqual(env.ref('dev_addons.menu_modules').name, 'Componentes')
        self.assertEqual(env.ref('dev_addons.menu_board').name, 'Tablero')
        self.assertEqual(env.ref('dev_addons.action_report_new').name, 'Nuevo reporte')
        self.assertEqual(env.ref('dev_addons.action_report_mine').name, 'Mis reportes')
        kinds = dict(env['dev.report'].fields_get(['kind'])['kind']['selection'])
        self.assertEqual(kinds['bug'], 'Algo no funciona')
        self.assertEqual(env.ref('dev_addons.menu_planning').name, 'Planificación')
        fields_es = env['project.task'].fields_get(['dev_reporter_id', 'dev_issue_type', 'dev_module_id'])
        self.assertEqual(fields_es['dev_reporter_id']['string'], 'Reportado por')
        self.assertEqual(fields_es['dev_module_id']['string'], 'Componente')
        self.assertEqual(dict(fields_es['dev_issue_type']['selection'])['bug'], 'Error')
        self.assertEqual(env['project.milestone'].fields_get(['dev_version'])['dev_version']['string'], 'Versión')
        self.assertEqual(env.ref('dev_addons.stage_todo').name, 'Por hacer')
        recap = env['dev.sprint'].get_views([(env.ref('dev_addons.sprint_recap_form').id, 'form')])
        self.assertIn('Terminadas por tipo', recap['views']['form']['arch'])
        with self.assertRaises(UserError) as error:
            self.sprint.with_env(env).action_open_complete_wizard()
        self.assertEqual(str(error.exception), 'Solo se pueden completar los sprints en curso.')
