# -*- coding: utf-8 -*-
{
    'name': 'Project Costing & Profitability',
    'version': '19.0.1.0.0',
    'category': 'Services/Project',
    'summary': 'Standalone Project Cost, Resource Allocation, Overhead & Profitability Management for Top Technologies',
    'description': """
TopTech Project Costing & Profitability System
===============================================
A self-contained Odoo 19 application for estimating, tracking, and analyzing project cost, profitability, overhead allocations, and support phase margins.

Key Features:
-------------
* Project Costing Master & Status Lifecycle
* Resource Cost Planning & Over-Allocation Constraint
* Direct Expense Tracking & Classification
* Monthly Overhead Pools & 5-Method Allocation Engine
* Post-Implementation Support Costing & Margins
* Monthly Cost Breakdown & Burn Rate Analysis
* Planned vs Actual Variance Tracking
* KPI Dashboard & Per-Project Summary Cards
* PDF Reports & Excel Exports
    """,
    'author': 'Top Technologies',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizards/overhead_allocation_wizard_views.xml',
        'wizards/project_export_wizard_views.xml',
        'wizards/project_comparison_wizard_views.xml',
        'views/project_costing_views.xml',
        'views/project_resource_views.xml',
        'views/project_expense_views.xml',
        'views/project_overhead_views.xml',
        'views/project_support_views.xml',
        'views/project_monthly_cost_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        'reports/project_costing_reports.xml',
        'reports/project_profitability_report_template.xml',
        'reports/resource_cost_report_template.xml',
        'reports/monthly_cost_report_template.xml',
        'reports/overhead_allocation_report_template.xml',
        'reports/support_profitability_report_template.xml',
        'reports/project_comparison_report_template.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'toptech_project_costing/static/src/css/dashboard.css',
            'toptech_project_costing/static/src/js/dashboard.js',
            'toptech_project_costing/static/src/xml/dashboard_template.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
