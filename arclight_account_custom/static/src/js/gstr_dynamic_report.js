/** @odoo-module **/

import { Component, useState, useRef, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

export class GstrDynamicReport extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dateFromRef = useRef("date_from");
        this.dateToRef = useRef("date_to");

        const today = new Date();
        const firstDayOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastDayOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);

        this.state = useState({
            date_range: "last-month",
            date_from: this.formatDate(firstDayOfLastMonth),
            date_to: this.formatDate(lastDayOfLastMonth),
            headers: [],
            sections: [],
            totals: {},
            tables: [],
            vouchers_summary: {},
            company_gstin: "",
            period_display: "",
            active_tab: "summary",
            search_query: "",
            loading: false,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    get reportType() {
        const tag = this.props.action.tag;
        if (tag === "gstr1_report") return "gstr1";
        if (tag === "gstr2_report") return "gstr2";
        if (tag === "gstr3b_report") return "gstr3b";
        if (tag === "gstr9_report") return "gstr9";
        return "gstr1";
    }

    formatDate(d) {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }

    formatNumber(num) {
        const val = parseFloat(num) || 0;
        return val.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    formatTallyAmount(val) {
        if (val === null || val === undefined || val === "" || val === 0) {
            return "";
        }
        const num = parseFloat(val);
        if (isNaN(num) || Math.abs(num) < 0.001) {
            return "";
        }
        const isNeg = num < 0;
        const absVal = Math.abs(num);
        const formatted = absVal.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        return isNeg ? `(-)${formatted}` : formatted;
    }

    formatCount(count) {
        if (!count || count === 0) return "";
        return String(count);
    }

    setActiveTab(tab) {
        this.state.active_tab = tab;
        this.state.search_query = "";
    }

    get activeTable() {
        if (!this.state.tables || this.state.tables.length === 0) {
            return null;
        }
        return this.state.tables.find(t => t.sheet_code === this.state.active_tab) || null;
    }

    getFilteredRows(table) {
        if (!table || !table.rows) return [];
        const q = (this.state.search_query || "").toLowerCase().trim();
        if (!q) return table.rows;
        return table.rows.filter(row =>
            row.some(cell => String(cell || "").toLowerCase().includes(q))
        );
    }

    onSearchInput(ev) {
        this.state.search_query = ev.target.value;
    }

    clearSearch() {
        this.state.search_query = "";
    }

    openSheet(sheetCode) {
        if (this.state.tables && this.state.tables.some(t => t.sheet_code === sheetCode)) {
            this.state.active_tab = sheetCode;
            this.state.search_query = "";
        }
    }

    onSectionClick(sec) {
        const code = sec.sheet_code || this.getSheetCodeForSection(sec);
        if (code && this.hasTable(code)) {
            this.openSheet(code);
        }
    }

    hasTable(code) {
        if (!this.state.tables || !code) return false;
        return this.state.tables.some(t => t.sheet_code === code);
    }

    isColNumeric(table, colIdx) {
        if (!table || !table.rows || table.rows.length === 0) return false;
        for (const row of table.rows) {
            const val = row[colIdx];
            if (val !== undefined && val !== null && val !== "") {
                const s = String(val).trim();
                if (s.endsWith("%")) return true;
                const clean = s.replace(/,/g, "").replace(/\./g, "").replace(/-/g, "");
                if (clean.length > 0 && /^\d+$/.test(clean)) return true;
            }
        }
        return false;
    }

    getSheetCodeForSection(sec) {
        if (!sec) return null;
        if (sec.sheet_code) return sec.sheet_code;
        const title = (sec.section || "").toLowerCase();
        if (title.includes("b2b")) return "b2b";
        if (title.includes("b2c(large)") || title.includes("b2cl")) return "b2cl";
        if (title.includes("b2c(small)") || title.includes("b2cs")) return "b2cs";
        if (title.includes("export")) return "exp";
        if (title.includes("registered") && !title.includes("unregistered")) return "cdnr";
        if (title.includes("unregistered")) return "cdnur";
        if (title.includes("nil") || title.includes("exempt")) return "exemp";
        if (title.includes("tax liability") || title.includes("advance received")) return "at";
        if (title.includes("adjustment of advance")) return "atadj";
        if (title.includes("hsn")) return "hsn.b2b";
        if (title.includes("doc")) return "docs";
        return null;
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "gstr.dynamic.report",
                "get_report_data",
                [this.reportType, this.state.date_from, this.state.date_to]
            );
            if (data) {
                this.state.headers = data.headers || [];
                this.state.sections = data.sections || [];
                this.state.totals = data.totals || {};
                this.state.tables = data.tables || [];
                this.state.vouchers_summary = data.vouchers_summary || {};
                this.state.company_gstin = data.company_gstin || "";
                this.state.period_display = data.period_display || "";
            }
        } catch (e) {
            console.error("Error loading GSTR report data", e);
        } finally {
            this.state.loading = false;
        }
    }

    async applyFilter(ev) {
        const filterType = ev.target.dataset.value;
        const today = new Date();
        let startDate, endDate;

        if (filterType === "month") {
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        } else if (filterType === "quarter") {
            const currentQuarter = Math.floor(today.getMonth() / 3);
            startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
            endDate = new Date(today.getFullYear(), (currentQuarter + 1) * 3, 0);
        } else if (filterType === "year") {
            startDate = new Date(today.getFullYear(), 0, 1);
            endDate = new Date(today.getFullYear(), 11, 31);
        } else if (filterType === "last-month") {
            startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        } else if (filterType === "last-quarter") {
            const lastQuarter = Math.floor((today.getMonth() - 3) / 3);
            startDate = new Date(today.getFullYear(), lastQuarter * 3, 1);
            endDate = new Date(today.getFullYear(), (lastQuarter + 1) * 3, 0);
        } else if (filterType === "last-year") {
            startDate = new Date(today.getFullYear() - 1, 0, 1);
            endDate = new Date(today.getFullYear() - 1, 11, 31);
        }

        if (startDate && endDate) {
            this.state.date_range = filterType;
            this.state.date_from = this.formatDate(startDate);
            this.state.date_to = this.formatDate(endDate);
            if (this.dateFromRef.el) {
                this.dateFromRef.el.value = this.state.date_from;
            }
            if (this.dateToRef.el) {
                this.dateToRef.el.value = this.state.date_to;
            }
            await this.loadData();
        }
    }

    async onCustomDateChange() {
        if (this.dateFromRef.el && this.dateFromRef.el.value) {
            this.state.date_from = this.dateFromRef.el.value;
        }
        if (this.dateToRef.el && this.dateToRef.el.value) {
            this.state.date_to = this.dateToRef.el.value;
        }
        this.state.date_range = "custom";
        await this.loadData();
    }

    async printPdf() {
        this.state.loading = true;
        try {
            const action = await this.orm.call(
                "gstr.dynamic.report",
                "export_pdf",
                [this.reportType, this.state.date_from, this.state.date_to]
            );
            if (action) {
                await this.action.doAction(action);
            }
        } catch (e) {
            console.error("Error printing GSTR PDF", e);
        } finally {
            this.state.loading = false;
        }
    }

    async exportXlsx() {
        try {
            const action = await this.orm.call(
                "gstr.dynamic.report",
                "export_xlsx",
                [this.reportType, this.state.date_from, this.state.date_to]
            );
            if (action) {
                await this.action.doAction(action);
            }
        } catch (e) {
            console.error("Error exporting GSTR Excel", e);
        }
    }
}

GstrDynamicReport.template = "gstr_dynamic_report_template";

actionRegistry.add("gstr1_report", GstrDynamicReport);
actionRegistry.add("gstr2_report", GstrDynamicReport);
actionRegistry.add("gstr3b_report", GstrDynamicReport);
actionRegistry.add("gstr9_report", GstrDynamicReport);
