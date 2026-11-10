# -*- coding: utf-8 -*-
"""Reports' "App" was a home-screen menu; it is now the installed application
(Sales, Inventory, Dev Projects...). Keep each report's app: the menu's module."""


def migrate(cr, version):
    cr.execute("""SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'dev_report' AND column_name = 'app_menu_id'""")
    if not cr.fetchone():
        return
    cr.execute("""
        UPDATE dev_report r
           SET app_id = m.id
          FROM ir_model_data d
          JOIN ir_module_module m ON m.name = d.module
         WHERE r.app_id IS NULL
           AND r.app_menu_id IS NOT NULL
           AND d.model = 'ir.ui.menu'
           AND d.res_id = r.app_menu_id
    """)
    cr.execute("ALTER TABLE dev_report DROP COLUMN app_menu_id")
