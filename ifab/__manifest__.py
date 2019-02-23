# -*- coding: utf-8 -*-
{
    'name': "ifab",

    'summary': """
        Developement specific for IFaB""",

    'description': """
        Developement specific for IFaB
    """,

    'author': "IFaB",
    'website': "http://www.ifab.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
        'depends': ['base','account','l10n_mx_edi','project','purchase','purchase_requisition', 'stock',],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/payments.xml',
        'views/project.xml',
        'views/purchase.xml',
        'views/stock_picking.xml',        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
