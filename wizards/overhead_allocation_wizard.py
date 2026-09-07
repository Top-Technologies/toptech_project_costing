# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ToptechOverheadAllocationWizard(models.TransientModel):
    _name = 'toptech.overhead.allocation.wizard'
    _description = 'Run Overhead Allocation Engine Wizard'

    overhead_id = fields.Many2one('toptech.project.overhead', string='Monthly Overhead Pool', required=True)
    allocation_method = fields.Selection([
        ('equal', 'Equal by project'),
        ('duration', 'By project duration'),
        ('resource_cost', 'By resource cost (default)'),
        ('percentage', 'By project percentage'),
        ('manual', 'Manual allocation'),
    ], string='Allocation Method', default='resource_cost', required=True)

    project_ids = fields.Many2many('toptech.project.costing', string='Target Projects', domain="[('status', 'in', ['cost_planning', 'approved', 'in_progress', 'support'])]")
    cost_type = fields.Selection([
        ('planned', 'Planned'),
        ('actual', 'Actual'),
    ], string='Cost Type', default='actual', required=True)

    @api.onchange('overhead_id')
    def _onchange_overhead_id(self):
        if not self.project_ids:
            self.project_ids = self.env['toptech.project.costing'].search([
                ('status', 'in', ['cost_planning', 'approved', 'in_progress', 'support'])
            ])

    def action_confirm_allocation(self):
        self.ensure_one()
        if not self.overhead_id:
            raise ValidationError(_("Please select an overhead pool."))
        
        projects = self.project_ids or self.env['toptech.project.costing'].search([
            ('status', 'in', ['cost_planning', 'approved', 'in_progress', 'support'])
        ])
        
        if not projects:
            raise ValidationError(_("No active projects found to allocate overhead."))

        pool_total = self.overhead_id.total_overhead
        if pool_total <= 0:
            raise ValidationError(_("The total overhead pool amount is zero."))

        # Clear existing allocations for this pool
        self.overhead_id.allocation_ids.unlink()

        allocations = []
        method = self.allocation_method

        if method == 'equal':
            count = len(projects)
            per_project = round(pool_total / count, 2)
            pct = round(100.0 / count, 2)
            for prj in projects:
                allocations.append((0, 0, {
                    'overhead_id': self.overhead_id.id,
                    'project_id': prj.id,
                    'allocation_method': method,
                    'allocation_percentage': pct,
                    'allocated_amount': per_project,
                    'cost_type': self.cost_type,
                    'notes': _("Equal allocation across %d active projects.") % count,
                }))

        elif method == 'duration':
            tot_duration = sum(p.duration_months for p in projects)
            if tot_duration <= 0:
                raise ValidationError(_("Total duration of selected projects is zero."))
            for prj in projects:
                pct = round((prj.duration_months / tot_duration) * 100.0, 2)
                amt = round(pool_total * (prj.duration_months / tot_duration), 2)
                allocations.append((0, 0, {
                    'overhead_id': self.overhead_id.id,
                    'project_id': prj.id,
                    'allocation_method': method,
                    'allocation_percentage': pct,
                    'allocated_amount': amt,
                    'cost_type': self.cost_type,
                    'notes': _("Allocated based on project duration (%.2f months / %.2f total).") % (prj.duration_months, tot_duration),
                }))

        elif method == 'resource_cost':
            tot_res = sum(p.resource_cost for p in projects)
            if tot_res <= 0:
                raise ValidationError(_("Total resource cost of selected projects is zero. Please ensure resources are planned."))
            for prj in projects:
                pct = round((prj.resource_cost / tot_res) * 100.0, 2)
                amt = round(pool_total * (prj.resource_cost / tot_res), 2)
                allocations.append((0, 0, {
                    'overhead_id': self.overhead_id.id,
                    'project_id': prj.id,
                    'allocation_method': method,
                    'allocation_percentage': pct,
                    'allocated_amount': amt,
                    'cost_type': self.cost_type,
                    'notes': _("Allocated based on resource cost (%.2f / %.2f total).") % (prj.resource_cost, tot_res),
                }))

        elif method == 'percentage':
            count = len(projects)
            pct = round(100.0 / count, 2)
            per_project = round(pool_total * (pct / 100.0), 2)
            for prj in projects:
                allocations.append((0, 0, {
                    'overhead_id': self.overhead_id.id,
                    'project_id': prj.id,
                    'allocation_method': method,
                    'allocation_percentage': pct,
                    'allocated_amount': per_project,
                    'cost_type': self.cost_type,
                    'notes': _("Percentage allocation (edit individual %% as needed)."),
                }))

        elif method == 'manual':
            count = len(projects)
            per_project = round(pool_total / count, 2)
            for prj in projects:
                allocations.append((0, 0, {
                    'overhead_id': self.overhead_id.id,
                    'project_id': prj.id,
                    'allocation_method': method,
                    'allocation_percentage': round(100.0 / count, 2),
                    'allocated_amount': per_project,
                    'cost_type': self.cost_type,
                    'notes': _("Manual allocation initial draft."),
                }))

        self.overhead_id.write({'allocation_ids': allocations})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'toptech.project.overhead',
            'res_id': self.overhead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
