# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class ToptechProjectSupport(models.Model):
    _name = 'toptech.project.support'
    _description = 'TopTech Post-Implementation Support Costing'
    _order = 'support_start_date desc, id desc'

    project_id = fields.Many2one('toptech.project.costing', string='Project', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True, readonly=True)
    name = fields.Char(string='Support Agreement Name', required=True)
    
    support_start_date = fields.Date(string='Support Start Date', required=True, default=fields.Date.today)
    support_end_date = fields.Date(string='Support End Date', required=True)
    number_of_months = fields.Float(string='Duration (Months)', compute='_compute_support_months', store=True, readonly=False, default=12.0)

    monthly_support_revenue = fields.Monetary(string='Monthly Support Revenue', currency_field='currency_id', required=True, default=0.0)
    
    support_employee_name = fields.Char(string='Support Employee')
    support_employee_monthly_cost = fields.Monetary(string='Support Employee Monthly Cost', currency_field='currency_id', default=0.0)
    support_allocation_percentage = fields.Float(string='Support Allocation %', default=100.0, required=True)
    
    monthly_support_cost = fields.Monetary(string='Monthly Support Employee Cost', compute='_compute_support_financials', store=True, currency_field='currency_id')
    support_overhead = fields.Monetary(string='Monthly Support Overhead', currency_field='currency_id', default=0.0)

    total_support_revenue = fields.Monetary(string='Total Support Revenue', compute='_compute_support_financials', store=True, currency_field='currency_id')
    total_support_cost = fields.Monetary(string='Total Support Cost', compute='_compute_support_financials', store=True, currency_field='currency_id')
    support_profit = fields.Monetary(string='Support Profit', compute='_compute_support_financials', store=True, currency_field='currency_id')
    support_margin = fields.Float(string='Support Margin (%)', compute='_compute_support_financials', store=True)

    notes = fields.Text(string='Notes')

    @api.depends('support_start_date', 'support_end_date')
    def _compute_support_months(self):
        for rec in self:
            if rec.support_start_date and rec.support_end_date:
                delta = relativedelta(rec.support_end_date, rec.support_start_date)
                months = delta.years * 12 + delta.months + (delta.days / 30.0)
                rec.number_of_months = round(max(0.1, months), 2)
            else:
                if not rec.number_of_months:
                    rec.number_of_months = 12.0

    @api.depends('support_employee_monthly_cost', 'support_allocation_percentage', 'monthly_support_revenue', 'support_overhead', 'number_of_months')
    def _compute_support_financials(self):
        for rec in self:
            rec.monthly_support_cost = round(rec.support_employee_monthly_cost * (rec.support_allocation_percentage / 100.0), 2)
            rec.total_support_revenue = round(rec.monthly_support_revenue * rec.number_of_months, 2)
            
            monthly_total_cost = rec.monthly_support_cost + rec.support_overhead
            rec.total_support_cost = round(monthly_total_cost * rec.number_of_months, 2)
            
            rec.support_profit = round(rec.total_support_revenue - rec.total_support_cost, 2)
            rec.support_margin = round((rec.support_profit / rec.total_support_revenue * 100.0), 2) if rec.total_support_revenue > 0 else 0.0
