{
    'name': 'PDF Stamp & Nextcloud Sync',
    'version': '17.0.7.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Stamp invoices with Odoo reference and sync PDF to Nextcloud automatically',
    'description': """
Automatically stamp vendor bills, customer invoices, credit notes and quotations
with their Odoo reference number, then push the PDF to Nextcloud — organised by
document type and year.
    """,
    'author': 'Walravens Justin',
    'website': '',
    'license': 'OPL-1',
    'depends': ['account', 'base_setup', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 9.90,
    'currency': 'EUR',
    'external_dependencies': {
        'python': ['pypdf', 'reportlab'],
    },
}
