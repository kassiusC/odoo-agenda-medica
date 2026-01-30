from odoo import models, fields

class Medico(models.Model):
    _name = 'mi.medico'
    _description = 'Médico'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    especialidad = fields.Selection([
        ('cardiologia', 'Cardiología'),
        ('pediatria', 'Pediatría'),
        ('dermatologia', 'Dermatología'),
        ('odontologia', 'Odontología'),
        ('clinica', 'Clínica General'),
    ], string='Especialidad', required=True)
    telefono = fields.Char(string='Teléfono')
    email = fields.Char(string='Correo electrónico')
    activo = fields.Boolean(string='Activo', default=True)
