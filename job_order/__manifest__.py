# -*- coding: utf-8 -*-
{
    'name': "Job order",
    'summary': """ """,
    'description': """
]    """,

    'author': "LC",
    'website': "https://www.ksolves.com/",
    'category': 'Sales',
    'version': '14.0.1.3.0',
    'application': True,
    'license': 'OPL-1',
    'currency': 'PKR',
    'price': '',
    'maintainer': 'Ali',
    'support': '',
    # any module necessary for this one to work correctly

    'depends': ['base', 'account','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/job_order_reports.xml'
    ],

    'external_dependencies': {
    },
}
