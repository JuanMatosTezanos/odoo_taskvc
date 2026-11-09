/** @odoo-module **/
// Top-bar icon (next to chat and activities): anyone sends a report to the
// dev team from any screen, or checks the ones they sent.
import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class ReportSystray extends Component {
    static template = "dev_addons.ReportSystray";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.action = useService("action");
    }

    get tooltip() {
        return _t("Report a problem or an idea");
    }

    newReport() {
        this.action.doAction("dev_addons.action_report_new");
    }

    myReports() {
        this.action.doAction("dev_addons.action_report_mine");
    }
}

registry.category("systray").add("dev_addons.report", { Component: ReportSystray }, { sequence: 30 });
