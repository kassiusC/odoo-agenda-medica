from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Persona(models.Model):
    _name = 'mi.persona'
    _description = 'Persona'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True, help="Nombre completo de la persona.")
    telefono = fields.Char(string='Teléfono', help="Número de contacto.")
    enviar_email = fields.Boolean(string="Enviar email", default=True)
    email = fields.Char(string='Correo electrónico', help="Correo de la persona.")
    activo = fields.Boolean(string='Activo', default=True, help="Indica si la persona está activa.")

    agendamiento_ids = fields.One2many(
        'mi.agendamiento',
        'persona_id',
        string="Agendamientos"
    )

    @api.constrains('enviar_email', 'email')
    def _check_email_required_if_send(self):
        for record in self:
            if record.enviar_email and not record.email:
                raise ValidationError(
                    f"La persona '{record.nombre}' tiene habilitado 'Enviar email' pero no tiene un correo electrónico configurado."
                )
