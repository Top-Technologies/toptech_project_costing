# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ToptechProjectMonthlyCost(models.Model):
    _name = 'toptech.project.monthly.cost'
    _description = 'TopTech Monthly Project Cost Breakdown'
    _order = 'month_date asc, id asc'

    project_id = fields.Many2one('toptech.project.costing', string='Project', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True, readonly=True)
    
    month_date = fields.Date(string='Month Date', required=True, default=fields.Date.today)
    month_name = fields.Char(string='Month / Year', compute='_compute_month_name', store=True)

    salary_cost = fields.Monetary(string='Salary / Resource Cost', currency_field='currency_id', default=0.0)
    expense_cost = fields.Monetary(string='Direct Expense Cost', currency_field='currency_id', default=0.0)
    overhead_cost = fields.Monetary(string='Allocated Overhead Cost', currency_field='currency_id', default=0.0)
    
    total_cost = fields.Monetary(string='Total Monthly Cost', compute='_compute_total_cost', store=True, currency_field='currency_id')
    
    cost_type = fields.Selection([
        ('planned', 'Planned'),
        ('actual', 'Actual'),
    ], string='Cost Type', default='actual', required=True)

    notes = fields.Text(string='Notes')

    @api.depends('month_date')
    def _compute_month_name(self):
        for rec in self:
            if rec.month_date:
                rec.month_name = rec.month_date.strftime('%B %Y')
            else:
                rec.month_name = ''

    @api.depends('salary_cost', 'expense_cost', 'overhead_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.salary_cost + rec.expense_cost + rec.overhead_cost
