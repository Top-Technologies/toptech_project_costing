# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ToptechProjectOverhead(models.Model):
    _name = 'toptech.project.overhead'
    _description = 'TopTech Monthly Overhead Pool'
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Overhead Period / Name', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    
    date_start = fields.Date(string='Period Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='Period End Date', required=True)

    rent = fields.Monetary(string='Rent', currency_field='currency_id', default=0.0)
    electricity = fields.Monetary(string='Electricity', currency_field='currency_id', default=0.0)
    internet = fields.Monetary(string='Internet', currency_field='currency_id', default=0.0)
    office_expenses = fields.Monetary(string='Office Expenses', currency_field='currency_id', default=0.0)
    administration = fields.Monetary(string='Administration', currency_field='currency_id', default=0.0)
    management = fields.Monetary(string='Management', currency_field='currency_id', default=0.0)

    total_overhead = fields.Monetary(string='Total Overhead Pool', compute='_compute_total_overhead', store=True, currency_field='currency_id')
    allocation_ids = fields.One2many('toptech.project.overhead.allocation', 'overhead_id', string='Overhead Allocations')
    
    allocated_total = fields.Monetary(string='Total Allocated', compute='_compute_allocated_total', store=True, currency_field='currency_id')
    unallocated_balance = fields.Monetary(string='Unallocated Balance', compute='_compute_allocated_total', store=True, currency_field='currency_id')

    notes = fields.Text(string='Notes')

    @api.depends('rent', 'electricity', 'internet', 'office_expenses', 'administration', 'management')
    def _compute_total_overhead(self):
        for rec in self:
            rec.total_overhead = sum([
                rec.rent, rec.electricity, rec.internet,
                rec.office_expenses, rec.administration, rec.management
            ])

    @api.depends('total_overhead', 'allocation_ids.allocated_amount')
    def _compute_allocated_total(self):
        for rec in self:
            tot = sum(rec.allocation_ids.mapped('allocated_amount'))
            rec.allocated_total = tot
            rec.unallocated_balance = rec.total_overhead - tot

    def action_open_allocation_wizard(self):
        """Opens the Overhead Allocation Wizard to distribute costs to projects."""
        self.ensure_one()
        return {
            'name': _('Run Overhead Allocation Engine'),
            'type': 'ir.actions.act_window',
            'res_model': 'toptech.overhead.allocation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_overhead_id': self.id,
                'default_allocation_method': 'resource_cost',
            }
        }
