from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


# Modelo Persona
class Persona(models.Model):
    _name = 'mi.persona'
    _description = 'Persona'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True, help="Nombre completo de la persona.")
    telefono = fields.Char(string='Teléfono', help="Número de contacto.")
    enviar_email = fields.Boolean(string="Enviar email", default=True)
    email = fields.Char(string='Correo electrónico', help="Correo de la persona.")
    activo = fields.Boolean(string='Activo', default=True, help="Indica si la persona está activa.")

    # Relación One2many hacia Agendamientos
    agendamiento_ids = fields.One2many(
        'mi.agendamiento',   # modelo destino
        'persona_id',        # campo inverso en Agendamiento
        string="Agendamientos"
    )

    # Validación: si enviar_email está marcado, email debe estar cargado
    @api.constrains('enviar_email', 'email')
    def _check_email_required_if_send(self):
        for record in self:
            if record.enviar_email and not record.email:
                raise ValidationError(
                    f"La persona '{record.nombre}' tiene habilitado 'Enviar email' pero no tiene un correo electrónico configurado."
                )

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


# Modelo Agendamiento
class Agendamiento(models.Model):
    _name = 'mi.agendamiento'
    _description = 'Agendamiento'
    _rec_name = 'titulo'

    titulo = fields.Char(string='Título', required=True, help="Título o motivo del agendamiento.")
    fecha = fields.Datetime(string='Fecha y hora', required=True, help="Fecha y hora del agendamiento.")
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='pendiente', help="Estado actual del agendamiento.")
    persona_id = fields.Many2one(
        'mi.persona',
        string='Persona',
        required=True,
        help="Persona asociada al agendamiento."
    )
    medico_id = fields.Many2one('mi.medico', string='Médico', required=True, help="Medico asociado al agendamiento.")

    def enviar_notificacion(self):
        for rec in self:
            persona = rec.persona_id
            if persona.enviar_email and persona.email:
                template = self.env.ref('mi_modulo.mail_template_agendamiento')
                template.send_mail(rec.id, force_send=True)

    def _check_email(self):
        for record in self:
            if not record.persona_id:
                raise UserError("Debe seleccionar una persona.")
            if record.persona_id.enviar_email and not record.persona_id.email:
                raise UserError(f"La persona '{record.persona_id.nombre}' tiene habilitado 'Enviar email' pero no tiene un correo electrónico configurado.")

    def action_confirmar(self):
        self._check_email()
        for record in self:
            record.estado = 'confirmado'
            record.enviar_notificacion()

    def action_cancelar(self):
        self._check_email()
        for record in self:
            record.estado = 'cancelado'
            record.enviar_notificacion()

    @api.model
    def create(self, vals):
        persona_id = vals.get("persona_id")
        if persona_id:
            persona = self.env["mi.persona"].browse(persona_id)
            if persona.enviar_email and not persona.email:
                raise UserError(f"La persona '{persona.nombre}' tiene habilitado 'Enviar email' pero no tiene un correo electrónico configurado.")
        return super().create(vals)
    
    def action_enviar_recordatorio(self):
        for record in self:
            persona = record.persona_id
            if persona.enviar_email and persona.email:
                template = self.env.ref('mi_modulo.mail_template_recordatorio')
                template.send_mail(record.id, force_send=True)
                _logger.info(f"Recordatorio enviado a {persona.email}")
            else:
                _logger.info(f"No se envió recordatorio a {persona.nombre}: enviar_email={persona.enviar_email}, email={persona.email}")
