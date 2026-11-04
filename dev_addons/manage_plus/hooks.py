# -*- coding: utf-8 -*-
"""Bring existing data in line with the issue tracker.

Used by the post-install hook (fresh install on a database that already has
"manage" data) and by the 17.0.2.0.0 migration (upgrade of manage_plus).
Every step only touches records that still need it, so running it twice is safe.
"""
import logging

from markupsafe import Markup, escape

from odoo import fields

_logger = logging.getLogger(__name__)

# Fields copied as-is when a bug or improvement becomes an issue.
COPY_FIELDS = [
    'name', 'description', 'history', 'definition_date', 'start_date', 'end_date',
    'is_paused', 'state', 'priority', 'color', 'sprint', 'story_points', 'date_deadline',
]


def post_init_hook(env):
    # In "manage", `active` meant "running", so finished sprints were archived.
    # It is a normal archive flag now: unarchive them all.
    sprints = env['manage.sprint'].with_context(active_test=False).search([])
    sprints.filtered(lambda s: not s.active).write({'active': True})
    _set_initial_sprint_states(env, sprints)
    migrate_to_issues(env)


def _set_initial_sprint_states(env, sprints):
    """Sprint status is new on install: derive it once from the dates.

    From then on sprints are started and completed by hand. Only the latest
    sprint running per project counts as running (one running sprint per project).
    """
    now = fields.Datetime.now()
    running_projects = set()
    for sprint in sprints.sorted(lambda s: s.start_date or now, reverse=True):
        if sprint.start_date and sprint.start_date <= now and (not sprint.end_date or sprint.end_date > now) \
                and sprint.project.id not in running_projects:
            state = 'running'
            running_projects.add(sprint.project.id)
        elif sprint.start_date and sprint.start_date <= now:
            state = 'closed'
        else:
            state = 'planned'
        sprint.state = state


def migrate_to_issues(env):
    env = env(context=dict(env.context, tracking_disable=True, mail_create_nolog=True,
                           mail_create_nosubscribe=True, mail_notrack=True))
    _set_project_keys(env)
    # Number existing tasks first, so they keep their creation order and the
    # notes written while moving bugs already show the new keys.
    env['manage.task'].search([('key', '=', False), ('project', '!=', False)], order='id')._assign_keys()
    _move_old_items(env, 'manage.bug', 'bug')
    _move_old_items(env, 'manage.improvement', 'improvement')
    _fill_issue_fields(env)
    env.flush_all()


def _set_project_keys(env):
    Project = env['manage.project'].with_context(active_test=False)
    for project in Project.search([('key', '=', False)], order='id'):
        project.key = Project._suggest_key(project.name)


def _move_old_items(env, model, issue_type):
    """Recreate every record of `model` as an issue of `issue_type`, then delete it.

    Comments, followers and activities move with it. Links between old items
    are written into the issue's chatter, since they pointed at old records.
    """
    Old = env[model]
    olds = Old.search([], order='id')
    if not olds:
        return
    Issue = env['manage.task']
    issue_model_id = env['ir.model']._get_id('manage.task')
    mapping = {}
    for old in olds:
        vals = {name: old._fields[name].convert_to_write(old[name], old) for name in COPY_FIELDS}
        vals.update({
            'issue_type': issue_type,
            'developer': [(6, 0, old.developer.ids)],
            'technology': [(6, 0, old.technology.ids)],
            'assignee': old.developer[:1].id,
            'reporter_id': old.create_uid.id,
            'project': old.project.id,
        })
        if issue_type == 'bug':
            vals['severity'] = old.severity or 'minor'
        new = Issue.create(vals)
        mapping[old.id] = new

        env['mail.message'].sudo().search([('model', '=', model), ('res_id', '=', old.id)]).write(
            {'model': 'manage.task', 'res_id': new.id})
        env['mail.followers'].sudo().search([('res_model', '=', model), ('res_id', '=', old.id)]).write(
            {'res_model': 'manage.task', 'res_id': new.id})
        env['mail.activity'].sudo().search([('res_model', '=', model), ('res_id', '=', old.id)]).write(
            {'res_model_id': issue_model_id, 'res_id': new.id})

    for old in olds:
        new = mapping[old.id]
        notes = [escape(f"Moved from the old {Old._description} {old.code}.")]
        linked = []
        if issue_type == 'bug':
            linked += [t.display_name for t in old.task_linked]
            linked += [mapping[b.id].display_name if b.id in mapping else b.code for b in old.bug_linked]
            linked += [i.code for i in old.improvement_linked]
        else:
            linked += [h.display_name for h in old.history_linked]
        if linked:
            notes.append(escape("Was linked to: " + ", ".join(linked)))
        new._message_log(body=Markup('<br/>').join(notes))

    _logger.info("Moved %s %s record(s) into issues", len(olds), model)
    olds.unlink()


def _fill_issue_fields(env):
    Issue = env['manage.task']
    Stage = env['manage.stage']

    for issue in Issue.search([('stage_id', '=', False)]):
        stage = Stage._for_state(issue.state, issue.project)
        if stage:
            # Same status category as the issue's state, so state and dates stay as they are.
            issue.stage_id = stage

    for issue in Issue.search([('assignee', '=', False), ('developer', '!=', False)]):
        issue.assignee = issue.developer[:1]

    for issue in Issue.search([('reporter_id', '=', False)]):
        issue.reporter_id = issue.create_uid

    Issue.search([('key', '=', False), ('project', '!=', False)], order='id')._assign_keys()
