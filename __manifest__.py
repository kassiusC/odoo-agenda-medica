{
    'name': 'Mi Primer Módulo',
    'version': '1.0',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vista.xml',
        'data/mail_templates.xml',
    ],
    'installable': True,
    'application': True,
}
