# -*- coding: utf-8 -*-
"""Reports became tickets with their own board (New, To Do, In Progress, Done)
instead of becoming Backlog issues. Existing ones keep their status, and every
ticket gets a number (TCK-1, TCK-2...). Issues already created from old reports
stay in their Backlog as they are."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # "Accepted" split into To Do / In Progress / Done (the old status column had it).
    cr.execute("""
        UPDATE dev_report
           SET state = CASE progress WHEN 'in_progress' THEN 'in_progress'
                                     WHEN 'done' THEN 'done'
                                     ELSE 'todo' END
         WHERE state = 'accepted'
    """)
    cr.execute("UPDATE dev_report SET done_date = write_date WHERE state = 'done' AND done_date IS NULL")
    env = api.Environment(cr, SUPERUSER_ID, {})
    Sequence = env['ir.sequence']
    cr.execute("SELECT id FROM dev_report WHERE key IS NULL ORDER BY create_date, id")
    for (ticket_id,) in cr.fetchall():
        cr.execute("UPDATE dev_report SET key = %s WHERE id = %s",
                   (Sequence.next_by_code('dev.ticket'), ticket_id))
