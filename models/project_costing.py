# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ToptechProjectCosting(models.Model):
    _name = 'toptech.project.costing'
    _description = 'TopTech Project Costing Master'
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Project Name', required=True, tracking=True)
    client_name = fields.Char(string='Client Name', required=True, tracking=True)
    reference = fields.Char(string='Project Reference', copy=False, default=lambda self: _('New'))
    contract_value = fields.Monetary(string='Contract Value', currency_field='currency_id', required=True, default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    planned_end_date = fields.Date(string='Planned End Date', required=True)
    actual_end_date = fields.Date(string='Actual End Date')
    duration_months = fields.Float(string='Duration (Months)', compute='_compute_duration_months', store=True, readonly=False)

    status = fields.Selection([
        ('draft', 'Draft'),
        ('cost_planning', 'Cost Planning'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('support', 'Support'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True, tracking=True)

    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user, required=True)
    notes = fields.Text(string='Notes')

    # Relations
    resource_ids = fields.One2many('toptech.project.resource', 'project_id', string='Project Resources')
    expense_ids = fields.One2many('toptech.project.expense', 'project_id', string='Direct Expenses')
    overhead_allocation_ids = fields.One2many('toptech.project.overhead.allocation', 'project_id', string='Overhead Allocations')
    support_ids = fields.One2many('toptech.project.support', 'project_id', string='Support Costing')
    monthly_cost_ids = fields.One2many('toptech.project.monthly.cost', 'project_id', string='Monthly Cost Breakdown')

    # Planned Cost Computes
    planned_resource_cost = fields.Monetary(string='Planned Resource Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    planned_expense_cost = fields.Monetary(string='Planned Expenses', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    planned_overhead_cost = fields.Monetary(string='Planned Overhead', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    planned_total_cost = fields.Monetary(string='Planned Total Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    planned_profit = fields.Monetary(string='Planned Profit', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    planned_margin = fields.Float(string='Planned Margin (%)', compute='_compute_cost_and_profitability', store=True)

    # Actual Cost Computes
    actual_resource_cost = fields.Monetary(string='Actual Resource Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    actual_expense_cost = fields.Monetary(string='Actual Expenses', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    actual_overhead_cost = fields.Monetary(string='Actual Overhead', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    actual_total_cost = fields.Monetary(string='Actual Total Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    actual_profit = fields.Monetary(string='Actual Profit', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    actual_margin = fields.Float(string='Actual Margin (%)', compute='_compute_cost_and_profitability', store=True)

    # Consolidated Effective Cost Computes
    resource_cost = fields.Monetary(string='Resource Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    expense_cost = fields.Monetary(string='Direct Expenses', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    overhead_cost = fields.Monetary(string='Allocated Overhead', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    project_profit = fields.Monetary(string='Project Profit', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    project_margin = fields.Float(string='Project Margin (%)', compute='_compute_cost_and_profitability', store=True)

    # Variances (Actual - Planned)
    resource_cost_variance = fields.Monetary(string='Resource Variance', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    expense_cost_variance = fields.Monetary(string='Expense Variance', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    overhead_cost_variance = fields.Monetary(string='Overhead Variance', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    total_cost_variance = fields.Monetary(string='Total Cost Variance', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    profit_variance = fields.Monetary(string='Profit Variance', compute='_compute_cost_and_profitability', store=True, currency_field='currency_id')
    margin_variance = fields.Float(string='Margin Variance (%)', compute='_compute_cost_and_profitability', store=True)

    is_over_budget = fields.Boolean(string='Over Budget', compute='_compute_cost_and_profitability', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('toptech.project.costing') or _('PRJ-%s') % fields.Datetime.now().strftime('%Y%m%d%H%M')
        return super(ToptechProjectCosting, self).create(vals_list)

    @api.depends('start_date', 'planned_end_date', 'actual_end_date', 'status')
    def _compute_duration_months(self):
        for rec in self:
            end_date = rec.actual_end_date if (rec.status in ['completed', 'closed'] and rec.actual_end_date) else rec.planned_end_date
            if rec.start_date and end_date:
                delta = relativedelta(end_date, rec.start_date)
                months = delta.years * 12 + delta.months + (delta.days / 30.0)
                rec.duration_months = round(max(0.1, months), 2)
            else:
                rec.duration_months = 0.0

    @api.depends(
        'contract_value',
        'resource_ids.planned_cost', 'resource_ids.actual_cost', 'resource_ids.resource_cost',
        'expense_ids.amount', 'expense_ids.planned_amount', 'expense_ids.actual_amount', 'expense_ids.cost_type',
        'overhead_allocation_ids.allocated_amount', 'overhead_allocation_ids.cost_type'
    )
    def _compute_cost_and_profitability(self):
        for rec in self:
            # 1. Planned Resource Cost
            planned_res = sum(rec.resource_ids.mapped('planned_cost'))
            actual_res = sum(rec.resource_ids.mapped('actual_cost'))
            res_tot = sum(rec.resource_ids.mapped('resource_cost')) if rec.resource_ids else (actual_res if actual_res > 0 else planned_res)

            # 2. Expenses
            planned_exp = 0.0
            actual_exp = 0.0
            for exp in rec.expense_ids:
                if exp.cost_type == 'planned':
                    planned_exp += exp.planned_amount or exp.amount
                elif exp.cost_type == 'actual':
                    actual_exp += exp.actual_amount or exp.amount
                else:
                    planned_exp += exp.planned_amount or exp.amount
                    actual_exp += exp.actual_amount or exp.amount

            # If expenses don't strictly set planned/actual amounts, fall back to total amount
            if planned_exp == 0.0 and rec.expense_ids:
                planned_exp = sum(e.amount for e in rec.expense_ids if e.cost_type == 'planned') or sum(e.amount for e in rec.expense_ids)
            if actual_exp == 0.0 and rec.expense_ids:
                actual_exp = sum(e.amount for e in rec.expense_ids if e.cost_type == 'actual') or sum(e.amount for e in rec.expense_ids)

            exp_tot = actual_exp if actual_exp > 0 else planned_exp

            # 3. Overhead Allocations
            planned_ovh = sum(o.allocated_amount for o in rec.overhead_allocation_ids if o.cost_type == 'planned')
            actual_ovh = sum(o.allocated_amount for o in rec.overhead_allocation_ids if o.cost_type == 'actual')
            if planned_ovh == 0.0 and rec.overhead_allocation_ids:
                planned_ovh = sum(o.allocated_amount for o in rec.overhead_allocation_ids)
            if actual_ovh == 0.0 and rec.overhead_allocation_ids:
                actual_ovh = sum(o.allocated_amount for o in rec.overhead_allocation_ids)

            ovh_tot = actual_ovh if actual_ovh > 0 else planned_ovh

            # Assign Planned
            rec.planned_resource_cost = planned_res
            rec.planned_expense_cost = planned_exp
            rec.planned_overhead_cost = planned_ovh
            rec.planned_total_cost = planned_res + planned_exp + planned_ovh
            rec.planned_profit = rec.contract_value - rec.planned_total_cost
            rec.planned_margin = (rec.planned_profit / rec.contract_value * 100.0) if rec.contract_value else 0.0

            # Assign Actual
            rec.actual_resource_cost = actual_res
            rec.actual_expense_cost = actual_exp
            rec.actual_overhead_cost = actual_ovh
            rec.actual_total_cost = actual_res + actual_exp + actual_ovh
            rec.actual_profit = rec.contract_value - rec.actual_total_cost
            rec.actual_margin = (rec.actual_profit / rec.contract_value * 100.0) if rec.contract_value else 0.0

            # Assign Effective Total
            rec.resource_cost = res_tot
            rec.expense_cost = exp_tot
            rec.overhead_cost = ovh_tot
            rec.total_cost = res_tot + exp_tot + ovh_tot
            rec.project_profit = rec.contract_value - rec.total_cost
            rec.project_margin = (rec.project_profit / rec.contract_value * 100.0) if rec.contract_value else 0.0

            # Variances (Actual - Planned)
            rec.resource_cost_variance = actual_res - planned_res
            rec.expense_cost_variance = actual_exp - planned_exp
            rec.overhead_cost_variance = actual_ovh - planned_ovh
            rec.total_cost_variance = rec.actual_total_cost - rec.planned_total_cost
            rec.profit_variance = rec.actual_profit - rec.planned_profit
            rec.margin_variance = rec.actual_margin - rec.planned_margin

            # Over Budget Status
            rec.is_over_budget = (rec.actual_total_cost > rec.planned_total_cost) or (rec.total_cost > rec.contract_value)

    # State Actions
    def action_cost_planning(self):
        self.write({'status': 'cost_planning'})

    def action_approve(self):
        self.write({'status': 'approved'})

    def action_start(self):
        self.write({'status': 'in_progress'})

    def action_complete(self):
        self.write({
            'status': 'completed',
            'actual_end_date': self.actual_end_date or fields.Date.today()
        })

    def action_support(self):
        self.write({'status': 'support'})

    def action_close(self):
        self.write({'status': 'closed'})

    def action_reset_draft(self):
        self.write({'status': 'draft'})

    def action_generate_monthly_cost(self):
        """Generates monthly breakdown lines based on duration and total project costs."""
        self.ensure_one()
        self.monthly_cost_ids.unlink()
        if not self.start_date or self.duration_months <= 0:
            raise ValidationError(_("Start date and duration must be set before generating monthly cost breakdown."))

        months_cnt = max(1, int(round(self.duration_months)))
        monthly_res = self.resource_cost / months_cnt
        monthly_exp = self.expense_cost / months_cnt
        monthly_ovh = self.overhead_cost / months_cnt

        curr_date = self.start_date
        lines = []
        for i in range(months_cnt):
            lines.append((0, 0, {
                'month_date': curr_date,
                'salary_cost': monthly_res,
                'expense_cost': monthly_exp,
                'overhead_cost': monthly_ovh,
                'cost_type': 'actual' if self.status in ['in_progress', 'completed', 'support', 'closed'] else 'planned',
                'notes': _("Generated monthly allocation for Month %d") % (i + 1),
            }))
            curr_date = curr_date + relativedelta(months=1)

        self.write({'monthly_cost_ids': lines})
        return True
