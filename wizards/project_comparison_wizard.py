# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ToptechProjectComparisonWizard(models.TransientModel):
    _name = 'toptech.project.comparison.wizard'
    _description = 'Project Comparison Report Wizard'

    project_ids = fields.Many2many('toptech.project.costing', string='Projects to Compare', required=True)
    report_type = fields.Selection([
        ('pdf', 'PDF Report'),
        ('excel', 'Excel Spreadsheet'),
    ], string='Export Format', default='pdf', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(ToptechProjectComparisonWizard, self).default_get(fields_list)
        projects = self.env['toptech.project.costing'].search([], limit=10)
        res['project_ids'] = [(6, 0, projects.ids)]
        return res

    def action_generate_report(self):
        self.ensure_one()
        if not self.project_ids:
            raise ValidationError(_("Please select at least one project for comparison."))

        if self.report_type == 'pdf':
            return self.env.ref('toptech_project_costing.action_report_project_comparison').report_action(self.project_ids)
        else:
            return self.env['toptech.project.export.wizard'].create({
                'project_ids': [(6, 0, self.project_ids.ids)],
                'report_type': 'comparison',
            }).action_export_excel()
