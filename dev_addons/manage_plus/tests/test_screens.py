# -*- coding: utf-8 -*-
"""Whole-app checks: every menu screen loads, and the base module still works."""
from datetime import timedelta

from lxml import etree

from odoo import fields
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval

VIEW_TYPES = {'tree': 'list'}


@tagged('post_install', '-at_install')
class TestScreens(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Some data so lists, kanbans and forms have records to show.
        cls.project = cls.env['manage.project'].create({'name': 'Screens'})
        cls.history = cls.env['manage.history'].create({'name': 'Epic', 'project': cls.project.id})
        cls.sprint = cls.env['manage.sprint'].create({'project': cls.project.id, 'duration': 7})
        cls.sprint.action_start()
        cls.dev = cls.env['res.partner'].create({
            'name': 'Screen Dev', 'is_dev': True, 'access_level': '10203040Z'})
        cls.issue = cls.env['manage.task'].create({
            'name': 'Screen issue', 'history': cls.history.id, 'sprint': cls.sprint.id,
            'assignee': cls.dev.id, 'issue_type': 'bug', 'severity': 'major'})

    # ------------------------------------------------------------------
    # Helpers that do what the web client does when a screen opens
    # ------------------------------------------------------------------

    def _spec(self, arch):
        """Fields spec of the top-level <field> nodes of a view (not sub-views)."""
        root = etree.fromstring(arch)
        names = {node.get('name') for node in root.iter('field')
                 if not any(a.tag == 'field' for a in node.iterancestors())}
        return {name: {} for name in names}

    def _open_action(self, action):
        """Load the views of a window action and read data the way the client does."""
        model = self.env[action['res_model']]
        ctx = action.get('context') or {}
        if isinstance(ctx, str):
            ctx = safe_eval(ctx, {'uid': self.env.uid, 'active_id': False})
        model = model.with_context(**{k: v for k, v in ctx.items()
                                      if not k.startswith('search_default_')})
        domain = action.get('domain') or []
        if isinstance(domain, str):
            domain = safe_eval(domain, {'uid': self.env.uid, 'active_id': False})

        view_types = [VIEW_TYPES.get(v, v) for v in action['view_mode'].split(',')]
        views = model.get_views([(False, vt) for vt in view_types] + [(False, 'search')])['views']

        # Default filters of the search view, like the client applies them.
        search = etree.fromstring(views['search']['arch'])
        for name, value in ctx.items():
            if name.startswith('search_default_') and value:
                node = search.find(f".//filter[@name='{name[15:]}']")
                self.assertIsNotNone(node, f"{action.get('name')}: default filter {name} missing")
                if node.get('domain'):
                    domain = domain + safe_eval(node.get('domain'), {'uid': self.env.uid})

        for vt in view_types:
            spec = self._spec(views[vt]['arch'])
            if vt in ('list', 'kanban'):
                model.web_search_read(domain, spec, limit=20)
                group_by = etree.fromstring(views[vt]['arch']).get('default_group_by') or ctx.get('group_by')
                if group_by:
                    model.web_read_group(domain, [group_by], [group_by])
            elif vt == 'form':
                record = model.search(domain, limit=1)
                if record:
                    record.web_read(spec)
                model.onchange({}, [], spec)  # the "New" button
            elif vt in ('pivot', 'graph'):
                model.read_group(domain, [], [])
            elif vt == 'calendar':
                model.search_read(domain, limit=5)

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_every_menu_opens(self):
        root = self.env.ref('manage.menu_root')
        menus = self.env['ir.ui.menu'].search([('id', 'child_of', root.id), ('action', '!=', False)])
        self.assertTrue(menus)
        opened = []
        for menu in menus:
            with self.subTest(menu=menu.complete_name):
                action = menu.action
                if action._name == 'ir.actions.server':
                    result = action.run()
                    self.assertEqual(result['type'], 'ir.actions.act_window')
                    result.setdefault('view_mode', 'form')
                    data = result
                else:
                    # The web client loads menu actions with sudo (/web/action/load).
                    data = action.sudo().read()[0]
                self._open_action(data)
                opened.append(menu.name)
        for expected in ('Board', 'Backlog', 'Projects', 'Sprints', 'Histories',
                         'Developers', 'Technologies', 'Board Columns', 'My Developer Profile'):
            self.assertIn(expected, opened)
        self.assertNotIn('All Issues', opened, "only one Board menu")

    def test_buttons_open_screens(self):
        project = self.project
        for method in ('action_view_histories', 'action_view_sprints', 'action_view_tasks',
                       'action_view_bugs', 'action_view_backlog'):
            with self.subTest(button=method):
                self._open_action(getattr(project, method)())
        for method in ('action_view_dev_tasks', 'action_view_dev_bugs', 'action_view_dev_improvements'):
            with self.subTest(button=method):
                action = getattr(self.dev, method)()
                self.assertTrue(action['res_model'])
        wizard = self.sprint.action_open_complete_wizard()
        self.assertEqual(wizard['res_model'], 'manage.sprint.complete')
        wizard = self.issue.action_open_complete_wizard()
        self.assertEqual(wizard['res_model'], 'manage.task.complete')

    def test_forms_save_from_scratch(self):
        """Create each main record through its form, like a user clicking New."""
        with Form(self.env['manage.project']) as f:
            f.name = 'From Form'
        project = f.record
        self.assertTrue(project.key)
        with Form(self.env['manage.history']) as f:
            f.name = 'Form epic'
            f.project = project
        with Form(self.env['manage.sprint']) as f:
            f.project = project
        self.assertEqual(f.record.state, 'planned')
        with Form(self.env['manage.task'].with_context(manage_board=True)) as f:
            f.name = 'Form issue'
            f.project = project
            f.issue_type = 'story'
            f.assignee = self.dev
            f.story_points = 5
        issue = f.record
        self.assertTrue(issue.key.startswith(project.key + '-'))
        self.assertEqual(issue.stage_id.state, 'todo')
        with Form(self.env['manage.technology']) as f:
            f.name = 'Screens Form Tech'
        with Form(self.env['res.partner'].with_context(default_is_dev=True),
                  view='manage.devs_partner_form') as f:
            f.name = 'New Dev'
            f.access_level = '99990000k'
        self.assertTrue(f.record.is_dev)

    # Base module features that must keep working -----------------------

    def test_base_features(self):
        # Developer counters and smart button domain.
        self.assertEqual(self.dev.dev_task_count, 1)
        action = self.dev.action_view_dev_tasks()
        self.assertIn(self.issue, self.env['manage.task'].search(action['domain']))
        # History technologies and task count.
        tech = self.env['manage.technology'].create({'name': 'Screens Tech'})
        self.issue.technology = tech
        self.assertEqual(self.history.used_technologies, tech)
        self.assertEqual(self.history.task_count, 1)
        self.assertEqual(tech.task_count, 1)
        self.assertEqual(tech.bug_count, 1)
        # Sprint end date follows start + duration.
        self.assertEqual(self.sprint.end_date, self.sprint.start_date + timedelta(days=7))
        # Pause / resume and the workflow buttons.
        self.issue.action_start()
        self.issue.action_toggle_pause()
        self.assertTrue(self.issue.is_paused)
        self.issue.action_toggle_pause()
        self.issue.action_review()
        self.assertEqual(self.issue.stage_id.state, 'review')
        self.issue.action_done()
        self.issue.action_reset()
        self.assertEqual((self.issue.state, self.issue.end_date), ('todo', False))
        self.assertLessEqual(self.issue.definition_date, fields.Datetime.now())

    def test_regular_user(self):
        """The same screens and flows as a normal internal user (access rights on)."""
        user = self.env['res.users'].create({
            'name': 'Regular', 'login': 'regular_screens',
            # Default groups, like a user created from Settings > Users.
        })
        self.env = self.env(user=user)
        self.project = self.project.with_user(user)
        self.test_every_menu_opens()

        issue = self.env['manage.task'].create({'name': 'Mine', 'project': self.project.id})
        issue.stage_id = self.env.ref('manage_plus.stage_in_progress')
        wizard = Form(self.env['manage.task.complete'].with_context(default_task_ids=issue.ids))
        wizard.save().action_confirm()
        self.assertFalse(issue.active)

        sprint = self.sprint.with_user(user)
        complete = Form(self.env['manage.sprint.complete'].with_context(default_sprint_id=sprint.id))
        complete.destination = 'backlog'
        complete.save().action_confirm()
        self.assertEqual(sprint.state, 'closed')
        self.env['manage.stage'].create({'name': 'QA', 'state': 'review'})
        self.env.user.partner_id.action_open_my_developer_profile()
        # A default user can turn their own contact into a developer and use Assign to Me.
        self.assertTrue(user.has_group('base.group_user'))
        with Form(user.partner_id, view='manage.devs_partner_form') as f:
            f.is_dev = True
            f.email = 'regular@example.com'  # Odoo requires it on a user's own contact
            f.access_level = '13572468r'
        mine = self.env['manage.task'].create({'name': 'For me', 'project': self.project.id})
        mine.action_assign_to_me()
        self.assertEqual(mine.assignee, user.partner_id)
