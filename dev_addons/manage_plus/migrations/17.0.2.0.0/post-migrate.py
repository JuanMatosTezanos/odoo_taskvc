# -*- coding: utf-8 -*-
"""Upgrade from 1.x: one issue model, project keys, stages, assignees."""
from odoo import SUPERUSER_ID, api

from odoo.addons.manage_plus.hooks import migrate_to_issues


def migrate(cr, version):
    if not version:
        return
    migrate_to_issues(api.Environment(cr, SUPERUSER_ID, {}))
