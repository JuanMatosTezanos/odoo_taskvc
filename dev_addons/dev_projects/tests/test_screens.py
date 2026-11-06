# -*- coding: utf-8 -*-
"""Whole-app checks: every Dev Projects screen opens like in the browser,
the Project app's screens still open, and a normal project user can work."""
from lxml import etree

from odoo.tests import Form, TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval

VIEW_TYPES = {'tree': 'list'}


@tagged('post_install', '-at_install')
class TestScreens(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Screens', 'dev_is_software': True})
        cls.milestone = cls.env['project.milestone'].create({'name': 'Epic', 'project_id': cls.project.id})
        cls.sprint = cls.env['dev.sprint'].create({'project_id': cls.project.id})
        cls.sprint.action_start()
        cls.issue = cls.env['project.task'].create({
            'name': 'Screen issue', 'project_id': cls.project.id, 'milestone_id': cls.milestone.id,
            'dev_sprint_id': cls.sprint.id, 'dev_assignee_id': cls.env.user.id,
            'dev_issue_type': 'bug', 'dev_severity': 'major'})
        cls.tech = cls.env['dev.technology'].create({'name': 'Screens Tech'})

    # Do what the web client does when a screen opens ----------------------

    def _spec(self, arch):
        root = etree.fromstring(arch)
        names = {node.get('name') for node in root.iter('field')
                 if not any(a.tag == 'field' for a in node.iterancestors())}
        return {name: {} for name in names}

    def _open_action(self, action):
        model = self.env[action['res_model']]
        ctx = action.get('context') or {}
        if isinstance(ctx, str):
            ctx = safe_eval(ctx, {'uid': self.env.uid, 'active_id': False})
        model = model.with_context(**{k: v for k, v in ctx.items() if not k.startswith('search_default_')})
        domain = action.get('domain') or []
        if isinstance(domain, str):
            domain = safe_eval(domain, {'uid': self.env.uid, 'active_id': False})

        views = action.get('views') or []
        explicit = {VIEW_TYPES.get(vt, vt): vid for vid, vt in views if vid}
        view_types = [VIEW_TYPES.get(v, v) for v in action['view_mode'].split(',')]
        search_id = action.get('search_view_id')
        if isinstance(search_id, (list, tuple)):
            search_id = search_id[0]
        result = model.get_views([(explicit.get(vt, False), vt) for vt in view_types]
                                 + [(search_id or False, 'search')])['views']

        search = etree.fromstring(result['search']['arch'])
        for name, value in ctx.items():
            if name.startswith('search_default_') and value:
                node = search.find(f".//filter[@name='{name[15:]}']")
                self.assertIsNotNone(node, f"{action.get('name')}: default filter {name} missing")
                if node.get('domain'):
                    domain = domain + safe_eval(node.get('domain'), {'uid': self.env.uid})

        for vt in view_types:
            spec = self._spec(result[vt]['arch'])
            if vt in ('list', 'kanban'):
                model.web_search_read(domain, spec, limit=20)
                group_by = etree.fromstring(result[vt]['arch']).get('default_group_by') or ctx.get('group_by')
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

    def _action_data(self, action):
        if action._name == 'ir.actions.server':
            data = action.run()
            data.setdefault('view_mode', 'form')
            return data
        # The web client loads menu actions with sudo (/web/action/load).
        data = action.sudo().read()[0]
        data['views'] = [(v.view_id.id, v.view_mode) for v in action.sudo().view_ids]
        return data

    def _open_menus(self, root_xmlid):
        root = self.env.ref(root_xmlid)
        menus = self.env['ir.ui.menu'].search([('id', 'child_of', root.id), ('action', '!=', False)])
        opened = []
        for menu in menus:
            with self.subTest(menu=menu.complete_name):
                self._open_action(self._action_data(menu.action))
                opened.append(menu.name)
        return opened

    # Tests ----------------------------------------------------------------

    def test_every_dev_menu_opens(self):
        opened = self._open_menus('dev_projects.menu_root')
        for expected in ('Board', 'Backlog', 'Projects', 'Milestones', 'Sprints', 'My Developer Profile',
                         'Developers', 'Technologies', 'Board Columns'):
            self.assertIn(expected, opened)

    def test_project_app_still_opens(self):
        opened = self._open_menus('project.menu_main_pm')
        self.assertIn('Projects', opened)
        # The project's task board in the Project app, with our additions.
        action = self.env['ir.actions.act_window']._for_xml_id('project.act_project_project_2_project_task_all')
        action['context'] = {'default_project_id': self.project.id, 'active_id': self.project.id}
        action['domain'] = [('project_id', '=', self.project.id)]
        self._open_action(action)
        self.env['project.task'].get_views([(self.env.ref('project.view_task_form2').id, 'form')])

    def test_buttons_open_screens(self):
        for method in ('action_dev_board', 'action_dev_open_issues', 'action_dev_bugs',
                       'action_dev_backlog', 'action_dev_sprints', 'action_dev_milestones'):
            with self.subTest(button=method):
                self._open_action(getattr(self.project, method)())
        self._open_action(self.sprint.action_view_issues())
        self.assertEqual(self.sprint.action_open_complete_wizard()['res_model'], 'dev.sprint.complete')
        self.assertEqual(self.issue.action_dev_open_complete_wizard()['res_model'], 'dev.task.complete')
        partner = self.env.user.partner_id
        self._open_action(partner.action_dev_view_issues())
        self.assertEqual(partner.action_dev_my_profile()['res_id'], partner.id)

    def test_forms_save_from_scratch(self):
        with Form(self.env['project.project'].with_context(default_dev_is_software=True)) as f:
            f.name = 'From Form'
        project = f.record
        self.assertTrue(project.dev_key)
        with Form(self.env['project.milestone'], view='dev_projects.milestone_form') as f:
            f.name = 'Form goal'
            f.project_id = project
        with Form(self.env['dev.sprint']) as f:
            f.project_id = project
        self.assertEqual((f.record.state, f.record.name), ('planned', 'Sprint 1'))
        with Form(self.env['project.task'].with_context(dev_board=True), view='project.view_task_form2') as f:
            f.name = 'Form issue'
            f.project_id = project
            f.dev_issue_type = 'story'
            f.dev_assignee_id = self.env.user
            f.dev_story_points = 5
        issue = f.record
        self.assertTrue(issue.dev_key.startswith(project.dev_key + '-'))
        self.assertEqual(issue.dev_status, 'todo')
        with Form(self.env['project.task'], view='dev_projects.task_quick_create_form') as f:
            f.name = 'Quick'
            f.project_id = project
        with Form(self.env['dev.technology']) as f:
            f.name = 'Screens Form Tech'
        with Form(self.env['res.partner'].with_context(default_dev_is_developer=True),
                  view='dev_projects.developer_form') as f:
            f.name = 'New Dev'
            f.dev_access_code = '99990000k'
        self.assertTrue(f.record.dev_is_developer)

    def test_regular_project_user(self):
        """The same screens and flows as a normal project user (access rights on)."""
        user = self.env['res.users'].create({'name': 'Regular', 'login': 'regular_dev_screens',
                                             'email': 'regular@example.com'})
        user.groups_id = [(4, self.env.ref('project.group_project_user').id)]
        self.project.message_subscribe(partner_ids=user.partner_id.ids)
        self.env = self.env(user=user)
        self.test_every_dev_menu_opens()

        project = self.project.with_user(user)
        issue = self.env['project.task'].with_context(dev_board=True).create(
            {'name': 'Mine', 'project_id': project.id})
        self.assertEqual(issue.dev_sprint_id, self.sprint, "created on the board: running sprint")
        issue.action_dev_assign_to_me()
        issue.action_dev_start()
        Form(self.env['dev.task.complete'].with_context(default_task_ids=issue.ids)).save().action_confirm()
        self.assertFalse(issue.active)

        complete = Form(self.env['dev.sprint.complete'].with_context(default_sprint_id=self.sprint.id))
        complete.destination = 'backlog'
        complete.save().action_confirm()
        self.assertEqual(self.sprint.with_user(user).state, 'closed')
        self.env['dev.sprint'].create({'project_id': project.id}).action_start()
        milestone = self.env['project.milestone'].create({'name': 'User goal', 'project_id': project.id})
        self._open_action(milestone.action_dev_view_issues())
        milestone.action_dev_complete()

        with Form(user.partner_id, view='dev_projects.developer_form') as f:
            f.dev_is_developer = True
            f.dev_access_code = '13572468r'
        self.assertTrue(user.partner_id.dev_is_developer)

    def test_menu_layout(self):
        """One "Projects" app: Odoo's menus under "Project", ours under "Dev Projects"."""
        app = self.env.ref('project.menu_main_pm')
        self.assertEqual(app.name, 'Projects')
        self.assertEqual(app.child_id.mapped('name'), ['Project', 'Dev Projects'])
        project_section = self.env.ref('dev_projects.menu_project_section')
        for xmlid in ('project.menu_projects', 'project.menu_project_management',
                      'project.menu_project_report', 'project.menu_project_config'):
            self.assertEqual(self.env.ref(xmlid).parent_id, project_section, xmlid)
        self.assertEqual(self.env.ref('dev_projects.menu_root').parent_id, app)
        self.assertEqual(self.env['ir.ui.menu'].search_count([('name', '=', 'Dev Projects'), ('parent_id', '=', False)]), 0,
                         "no separate Dev Projects app")
        # Dev Projects > Configuration has Project's settings and configuration too.
        config = self.env.ref('dev_projects.menu_config').child_id.mapped('name')
        for name in ('Settings', 'Board Columns', 'Tags', 'Activity Types'):
            self.assertIn(name, config)

    def test_settings(self):
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(settings.dev_default_columns)
        settings.write({'dev_sprint_duration': 10, 'dev_default_columns': False,
                        'dev_tech_image_dir': '/somewhere'})
        settings.execute()
        self.assertFalse(self.env['res.config.settings'].create({}).dev_default_columns)
        self.assertEqual(self.env['dev.sprint'].create({'project_id': self.project.id}).duration, 10)
        self.assertFalse(self.env['project.project'].create({'name': 'No Columns', 'dev_is_software': True}).type_ids)
        self.assertEqual(self.env['ir.config_parameter'].get_param('dev_projects.tech_image_dir'), '/somewhere')
        # The settings page (with our section) opens.
        self.env['res.config.settings'].get_views([(False, 'form')])
