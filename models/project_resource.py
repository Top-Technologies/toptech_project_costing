# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ToptechProjectResource(models.Model):
    _name = 'toptech.project.resource'
    _description = 'TopTech Project Resource Planning'
    _order = 'project_id desc, id asc'

    project_id = fields.Many2one('toptech.project.costing', string='Project', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True, readonly=True)
    name = fields.Char(string='Resource Name', required=True)
    position = fields.Char(string='Position / Role')
    monthly_cost = fields.Monetary(string='Monthly Salary/Cost', currency_field='currency_id', required=True, default=0.0)
    allocation_percentage = fields.Float(string='Allocation %', required=True, default=100.0)
    
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    number_of_months = fields.Float(string='Number of Months', compute='_compute_number_of_months', store=True, readonly=False, default=1.0)
    
    cost_type = fields.Selection([
        ('planned', 'Planned'),
        ('actual', 'Actual'),
        ('both', 'Both Planned & Actual'),
    ], string='Cost Type', default='both', required=True)

    planned_cost = fields.Monetary(string='Planned Cost', compute='_compute_costs', store=True, readonly=False, currency_field='currency_id')
    actual_cost = fields.Monetary(string='Actual Cost', compute='_compute_costs', store=True, readonly=False, currency_field='currency_id')
    resource_cost = fields.Monetary(string='Resource Cost', compute='_compute_costs', store=True, currency_field='currency_id')
    
    allow_over_allocation = fields.Boolean(string='Admin Override Allocation Limit', default=False, help="Allow total resource allocation across projects to exceed 100%.")
    notes = fields.Text(string='Notes')

    @api.depends('start_date', 'end_date', 'project_id.start_date', 'project_id.planned_end_date', 'project_id.duration_months')
    def _compute_number_of_months(self):
        for rec in self:
            s_date = rec.start_date or (rec.project_id.start_date if rec.project_id else None)
            e_date = rec.end_date or (rec.project_id.planned_end_date if rec.project_id else None)
            if s_date and e_date:
                delta = relativedelta(e_date, s_date)
                months = delta.years * 12 + delta.months + (delta.days / 30.0)
                rec.number_of_months = round(max(0.1, months), 2)
            elif rec.project_id and rec.project_id.duration_months:
                rec.number_of_months = rec.project_id.duration_months
            else:
                if not rec.number_of_months:
                    rec.number_of_months = 1.0

    @api.depends('monthly_cost', 'allocation_percentage', 'number_of_months', 'cost_type')
    def _compute_costs(self):
        for rec in self:
            calc_planned = rec.monthly_cost * (rec.allocation_percentage / 100.0) * rec.number_of_months
            rec.planned_cost = round(calc_planned, 2)
            
            if not rec.actual_cost or rec.actual_cost == 0.0:
                rec.actual_cost = rec.planned_cost

            if rec.cost_type == 'planned':
                rec.resource_cost = rec.planned_cost
            elif rec.cost_type == 'actual':
                rec.resource_cost = rec.actual_cost
            else:
                rec.resource_cost = rec.actual_cost if rec.actual_cost > 0 else rec.planned_cost

    @api.constrains('name', 'allocation_percentage', 'start_date', 'end_date', 'project_id', 'allow_over_allocation')
    def _check_allocation_percentage_limit(self):
        for rec in self:
            if rec.allow_over_allocation:
                continue
            if not rec.name:
                continue
            
            # Find all resource records with matching name in active projects
            domain = [
                ('name', '=ilike', rec.name.strip()),
                ('project_id.status', 'in', ['cost_planning', 'approved', 'in_progress', 'support'])
            ]
            all_resources = self.search(domain)
            total_alloc = sum(r.allocation_percentage for r in all_resources)

            if total_alloc > 100.0:
                raise ValidationError(_(
                    "Over-Allocation Error for resource '%s'!\n"
                    "Total allocation across active projects is %.2f%%, which exceeds the maximum limit of 100.00%%.\n"
                    "Please reduce the allocation percentage or check 'Admin Override Allocation Limit' if authorized."
                ) % (rec.name, total_alloc))
