{
    'name': 'Agenda Medica',
    'version': '1.0',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/persona_views.xml', 
        'views/medico_views.xml', 
        'views/agendamiento_views.xml',
        'data/mail_templates.xml',
        'data/ir_cron.xml',
        'reports/agendamiento_report.xml', 
    ],
    'installable': True,
    'application': True,
}
