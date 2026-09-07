# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import io
import base64


class ToptechProjectExportWizard(models.TransientModel):
    _name = 'toptech.project.export.wizard'
    _description = 'Export Project Reports to Excel'

    report_type = fields.Selection([
        ('profitability', 'Project Profitability Report'),
        ('resource', 'Resource Cost Report'),
        ('monthly', 'Monthly Cost Breakdown Report'),
        ('overhead', 'Overhead Allocation Report'),
        ('support', 'Support Profitability Report'),
        ('comparison', 'Project Side-by-Side Comparison Report'),
    ], string='Report Type', default='profitability', required=True)

    project_ids = fields.Many2many('toptech.project.costing', string='Projects', help="Leave empty to include all projects")
    excel_file = fields.Binary(string='Excel File', readonly=True)
    file_name = fields.Char(string='File Name', readonly=True)

    def action_export_excel(self):
        self.ensure_one()
        projects = self.project_ids or self.env['toptech.project.costing'].search([])
        if not projects and self.report_type != 'overhead':
            raise ValidationError(_("No projects found to export."))

        output = io.BytesIO()
        try:
            import xlsxwriter
        except ImportError:
            raise ValidationError(_("xlsxwriter library is not installed on the server."))

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Styles
        title_style = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1f4e78', 'font_color': '#FFFFFF'})
        header_style = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#2e75b6', 'font_color': '#FFFFFF', 'border': 1})
        cell_style = workbook.add_format({'font_size': 10, 'align': 'left', 'valign': 'vcenter', 'border': 1})
        num_style = workbook.add_format({'font_size': 10, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.00'})
        pct_style = workbook.add_format({'font_size': 10, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'num_format': '0.00"%'})
        total_style = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#d9e1f2', 'border': 1, 'num_format': '#,##0.00'})

        sheet_name = dict(self._fields['report_type'].selection).get(self.report_type, 'Export')[:31]
        worksheet = workbook.add_worksheet(sheet_name)

        if self.report_type == 'profitability':
            worksheet.merge_range('A1:L1', 'TopTech Project Profitability Report', title_style)
            headers = ['Project Reference', 'Project Name', 'Client', 'Status', 'Duration (Mos)', 'Contract Value', 'Resource Cost', 'Expenses', 'Overhead', 'Total Cost', 'Profit', 'Margin %']
            for col_idx, text in enumerate(headers):
                worksheet.write(2, col_idx, text, header_style)
                worksheet.set_column(col_idx, col_idx, 18)

            row = 3
            for prj in projects:
                worksheet.write(row, 0, prj.reference or '', cell_style)
                worksheet.write(row, 1, prj.name or '', cell_style)
                worksheet.write(row, 2, prj.client_name or '', cell_style)
                worksheet.write(row, 3, prj.status or '', cell_style)
                worksheet.write(row, 4, prj.duration_months, num_style)
                worksheet.write(row, 5, prj.contract_value, num_style)
                worksheet.write(row, 6, prj.resource_cost, num_style)
                worksheet.write(row, 7, prj.expense_cost, num_style)
                worksheet.write(row, 8, prj.overhead_cost, num_style)
                worksheet.write(row, 9, prj.total_cost, num_style)
                worksheet.write(row, 10, prj.project_profit, num_style)
                worksheet.write(row, 11, prj.project_margin / 100.0, pct_style)
                row += 1

            worksheet.write(row, 0, 'Total', header_style)
            worksheet.write(row, 5, sum(p.contract_value for p in projects), total_style)
            worksheet.write(row, 6, sum(p.resource_cost for p in projects), total_style)
            worksheet.write(row, 7, sum(p.expense_cost for p in projects), total_style)
            worksheet.write(row, 8, sum(p.overhead_cost for p in projects), total_style)
            worksheet.write(row, 9, sum(p.total_cost for p in projects), total_style)
            worksheet.write(row, 10, sum(p.project_profit for p in projects), total_style)

        elif self.report_type == 'resource':
            worksheet.merge_range('A1:I1', 'TopTech Resource Cost Report', title_style)
            headers = ['Project Name', 'Resource Name', 'Position / Role', 'Monthly Salary', 'Allocation %', 'Months', 'Planned Cost', 'Actual Cost', 'Resource Cost']
            for col_idx, text in enumerate(headers):
                worksheet.write(2, col_idx, text, header_style)
                worksheet.set_column(col_idx, col_idx, 20)

            row = 3
            resources = self.env['toptech.project.resource'].search([('project_id', 'in', projects.ids)])
            for res in resources:
                worksheet.write(row, 0, res.project_id.name or '', cell_style)
                worksheet.write(row, 1, res.name or '', cell_style)
                worksheet.write(row, 2, res.position or '', cell_style)
                worksheet.write(row, 3, res.monthly_cost, num_style)
                worksheet.write(row, 4, res.allocation_percentage / 100.0, pct_style)
                worksheet.write(row, 5, res.number_of_months, num_style)
                worksheet.write(row, 6, res.planned_cost, num_style)
                worksheet.write(row, 7, res.actual_cost, num_style)
                worksheet.write(row, 8, res.resource_cost, num_style)
                row += 1

        elif self.report_type == 'monthly':
            worksheet.merge_range('A1:G1', 'TopTech Monthly Cost Breakdown Report', title_style)
            headers = ['Project Name', 'Month / Year', 'Month Date', 'Salary Cost', 'Expense Cost', 'Overhead Cost', 'Total Monthly Cost']
            for col_idx, text in enumerate(headers):
                worksheet.write(2, col_idx, text, header_style)
                worksheet.set_column(col_idx, col_idx, 20)

            row = 3
            monthly_lines = self.env['toptech.project.monthly.cost'].search([('project_id', 'in', projects.ids)])
            for line in monthly_lines:
                worksheet.write(row, 0, line.project_id.name or '', cell_style)
                worksheet.write(row, 1, line.month_name or '', cell_style)
                worksheet.write(row, 2, str(line.month_date or ''), cell_style)
                worksheet.write(row, 3, line.salary_cost, num_style)
                worksheet.write(row, 4, line.expense_cost, num_style)
                worksheet.write(row, 5, line.overhead_cost, num_style)
                worksheet.write(row, 6, line.total_cost, num_style)
                row += 1

        elif self.report_type == 'overhead':
            worksheet.merge_range('A1:F1', 'TopTech Overhead Allocation Report', title_style)
            headers = ['Overhead Pool Name', 'Project Name', 'Allocation Method', 'Allocation %', 'Allocated Amount', 'Cost Type']
            for col_idx, text in enumerate(headers):
                worksheet.write(2, col_idx, text, header_style)
                worksheet.set_column(col_idx, col_idx, 22)

            row = 3
            allocations = self.env['toptech.project.overhead.allocation'].search([])
            for alloc in allocations:
                worksheet.write(row, 0, alloc.overhead_id.name or '', cell_style)
                worksheet.write(row, 1, alloc.project_id.name or '', cell_style)
                worksheet.write(row, 2, alloc.allocation_method or '', cell_style)
                worksheet.write(row, 3, alloc.allocation_percentage / 100.0, pct_style)
                worksheet.write(row, 4, alloc.allocated_amount, num_style)
                worksheet.write(row, 5, alloc.cost_type or '', cell_style)
                row += 1

        elif self.report_type == 'support':
            worksheet.merge_range('A1:I1', 'TopTech Support Phase Profitability Report', title_style)
            headers = ['Project Name', 'Support Agreement', 'Duration (Mos)', 'Monthly Revenue', 'Total Revenue', 'Monthly Employee Cost', 'Monthly Overhead', 'Total Support Cost', 'Support Profit', 'Support Margin %']
            for col_idx, text in enumerate(headers):
                worksheet.write(2, col_idx, text, header_style)
                worksheet.set_column(col_idx, col_idx, 20)

            row = 3
            supports = self.env['toptech.project.support'].search([('project_id', 'in', projects.ids)])
            for sup in supports:
                worksheet.write(row, 0, sup.project_id.name or '', cell_style)
                worksheet.write(row, 1, sup.name or '', cell_style)
                worksheet.write(row, 2, sup.number_of_months, num_style)
                worksheet.write(row, 3, sup.monthly_support_revenue, num_style)
                worksheet.write(row, 4, sup.total_support_revenue, num_style)
                worksheet.write(row, 5, sup.monthly_support_cost, num_style)
                worksheet.write(row, 6, sup.support_overhead, num_style)
                worksheet.write(row, 7, sup.total_support_cost, num_style)
                worksheet.write(row, 8, sup.support_profit, num_style)
                worksheet.write(row, 9, sup.support_margin / 100.0, pct_style)
                row += 1

        elif self.report_type == 'comparison':
            worksheet.merge_range(0, 0, 0, len(projects) + 1, 'TopTech Side-by-Side Project Comparison Report', title_style)
            metrics = [
                ('Client', lambda p: p.client_name or '', cell_style),
                ('Status', lambda p: p.status or '', cell_style),
                ('Duration (Months)', lambda p: p.duration_months, num_style),
                ('Contract Value', lambda p: p.contract_value, num_style),
                ('Resource Cost', lambda p: p.resource_cost, num_style),
                ('Direct Expenses', lambda p: p.expense_cost, num_style),
                ('Allocated Overhead', lambda p: p.overhead_cost, num_style),
                ('Total Project Cost', lambda p: p.total_cost, num_style),
                ('Project Profit', lambda p: p.project_profit, num_style),
                ('Project Margin (%)', lambda p: p.project_margin / 100.0, pct_style),
                ('Total Cost Variance', lambda p: p.total_cost_variance, num_style),
            ]
            worksheet.write(2, 0, 'Metric / KPI', header_style)
            worksheet.set_column(0, 0, 25)
            for idx, prj in enumerate(projects):
                worksheet.write(2, idx + 1, prj.name, header_style)
                worksheet.set_column(idx + 1, idx + 1, 22)

            row = 3
            for label, func, fmt in metrics:
                worksheet.write(row, 0, label, cell_style)
                for idx, prj in enumerate(projects):
                    worksheet.write(row, idx + 1, func(prj), fmt)
                row += 1

        workbook.close()
        output.seek(0)

        fname = f"TopTech_{self.report_type.capitalize()}_Report.xlsx"
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'file_name': fname,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=toptech.project.export.wizard&id={self.id}&field=excel_file&filename_field=file_name&download=true',
            'target': 'self',
        }
