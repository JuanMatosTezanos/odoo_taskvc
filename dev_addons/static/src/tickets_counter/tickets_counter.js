/** @odoo-module **/
// Shows how many new tickets are waiting next to Dev Projects > Work > Tickets,
// e.g. "Tickets 3". Only for the team (devs and IT), only inside the Projects app.
import { onMounted, useState } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.devTickets = useState({ count: 0 });
        this.devOrm = useService("orm");
        this.devUser = useService("user");
        const refresh = () => this.devRefreshTickets();
        onMounted(refresh);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", refresh);
        useBus(this.env.bus, "MENUS:APP-CHANGED", refresh);
    },

    get devTicketCount() {
        return this.devTickets.count;
    },

    async devRefreshTickets() {
        const app = this.menuService.getCurrentApp();
        if (!app || app.xmlid !== "project.menu_main_pm") {
            return;
        }
        if (!(await this.devUser.hasGroup("project.group_project_user"))) {
            return;
        }
        this.devTickets.count = await this.devOrm.silent.searchCount("dev.report", [["state", "=", "new"]]);
    },
});
