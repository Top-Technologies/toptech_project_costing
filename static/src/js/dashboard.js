/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ToptechProjectDashboard extends Component {
    static template = "toptech_project_costing.ProjectDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            kpi: {
                total_projects: 0,
                active_projects: 0,
                total_contract_value: 0,
                total_planned_cost: 0,
                total_actual_cost: 0,
                expected_profit: 0,
                actual_profit: 0,
                avg_margin: 0,
                monthly_cost: 0,
                over_budget_count: 0,
            },
            projects: [],
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const projects = await this.orm.searchRead(
            "toptech.project.costing",
            [],
            [
                "id", "name", "client_name", "reference", "contract_value",
                "planned_total_cost", "actual_total_cost", "total_cost",
                "planned_profit", "actual_profit", "project_profit",
                "planned_margin", "actual_margin", "project_margin",
                "duration_months", "status", "is_over_budget", "currency_id"
            ]
        );

        let totalContract = 0;
        let totalPlannedCost = 0;
        let totalActualCost = 0;
        let expectedProfit = 0;
        let actualProfit = 0;
        let activeCount = 0;
        let overBudgetCount = 0;
        let totalMargin = 0;

        projects.forEach(p => {
            totalContract += p.contract_value || 0;
            totalPlannedCost += p.planned_total_cost || 0;
            totalActualCost += p.actual_total_cost || p.total_cost || 0;
            expectedProfit += p.planned_profit || 0;
            actualProfit += p.project_profit || 0;
            totalMargin += p.project_margin || 0;
            if (['cost_planning', 'approved', 'in_progress', 'support'].includes(p.status)) {
                activeCount++;
            }
            if (p.is_over_budget) {
                overBudgetCount++;
            }
        });

        const avgMargin = projects.length ? (totalMargin / projects.length) : 0;
        const totalDuration = projects.reduce((acc, p) => acc + (p.duration_months || 1), 0);
        const monthlyCost = totalDuration > 0 ? (totalActualCost / totalDuration) : 0;

        this.state.kpi = {
            total_projects: projects.length,
            active_projects: activeCount,
            total_contract_value: totalContract,
            total_planned_cost: totalPlannedCost,
            total_actual_cost: totalActualCost,
            expected_profit: expectedProfit,
            actual_profit: actualProfit,
            avg_margin: avgMargin.toFixed(1),
            monthly_cost: monthlyCost,
            over_budget_count: overBudgetCount,
        };

        this.state.projects = projects;
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value || 0);
    }

    openProject(id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'toptech.project.costing',
            res_id: id,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    openNewProject() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'toptech.project.costing',
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

registry.category("actions").add("toptech_project_costing.dashboard", ToptechProjectDashboard);
