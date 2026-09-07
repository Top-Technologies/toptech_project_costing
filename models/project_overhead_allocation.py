# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ToptechProjectOverheadAllocation(models.Model):
    _name = 'toptech.project.overhead.allocation'
    _description = 'TopTech Overhead Project Allocation'
    _order = 'overhead_id desc, allocated_amount desc'

    overhead_id = fields.Many2one('toptech.project.overhead', string='Monthly Overhead Pool', required=True, ondelete='cascade')
    project_id = fields.Many2one('toptech.project.costing', string='Project', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='overhead_id.currency_id', store=True, readonly=True)
    
    allocation_method = fields.Selection([
        ('equal', 'Equal by project'),
        ('duration', 'By project duration'),
        ('resource_cost', 'By resource cost (default)'),
        ('percentage', 'By project percentage'),
        ('manual', 'Manual allocation'),
    ], string='Allocation Method', default='resource_cost', required=True)

    allocation_percentage = fields.Float(string='Allocation %', default=0.0)
    allocated_amount = fields.Monetary(string='Allocated Amount', currency_field='currency_id', required=True, default=0.0)
    
    cost_type = fields.Selection([
        ('planned', 'Planned'),
        ('actual', 'Actual'),
    ], string='Cost Type', default='actual', required=True)

    notes = fields.Text(string='Notes')

    @api.onchange('allocation_percentage', 'overhead_id', 'allocation_method')
    def _onchange_allocation_percentage(self):
        if self.allocation_method == 'percentage' and self.overhead_id and self.allocation_percentage:
            self.allocated_amount = round(self.overhead_id.total_overhead * (self.allocation_percentage / 100.0), 2)
