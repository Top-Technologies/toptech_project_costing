# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ToptechProjectExpense(models.Model):
    _name = 'toptech.project.expense'
    _description = 'TopTech Direct Project Expenses'
    _order = 'date desc, id desc'

    project_id = fields.Many2one('toptech.project.costing', string='Project', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True, readonly=True)
    
    expense_type = fields.Selection([
        ('travel', 'Travel'),
        ('transportation', 'Transportation'),
        ('accommodation', 'Accommodation'),
        ('communication', 'Communication'),
        ('client_meeting', 'Client meeting'),
        ('training', 'Training'),
        ('software', 'Software'),
        ('hardware', 'Hardware'),
        ('subcontractor', 'Subcontractor'),
        ('other', 'Other'),
    ], string='Expense Type', required=True, default='other')

    description = fields.Char(string='Description', required=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True, default=0.0)
    date = fields.Date(string='Expense Date', default=fields.Date.today, required=True)
    
    cost_type = fields.Selection([
        ('planned', 'Planned'),
        ('actual', 'Actual'),
    ], string='Planned / Actual', default='actual', required=True)

    planned_amount = fields.Monetary(string='Planned Amount', currency_field='currency_id', compute='_compute_amounts', store=True, readonly=False)
    actual_amount = fields.Monetary(string='Actual Amount', currency_field='currency_id', compute='_compute_amounts', store=True, readonly=False)

    notes = fields.Text(string='Notes')

    @api.depends('amount', 'cost_type')
    def _compute_amounts(self):
        for rec in self:
            if rec.cost_type == 'planned':
                if not rec.planned_amount:
                    rec.planned_amount = rec.amount
                if not rec.actual_amount:
                    rec.actual_amount = 0.0
            else:
                if not rec.actual_amount:
                    rec.actual_amount = rec.amount
                if not rec.planned_amount:
                    rec.planned_amount = rec.amount
