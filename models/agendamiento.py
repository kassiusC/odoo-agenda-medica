from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)

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
    persona_id = fields.Many2one('mi.persona', string='Persona', required=True, help="Persona asociada al agendamiento.")
    medico_id = fields.Many2one('mi.medico', string='Médico', required=True, help="Medico asociado al agendamiento.")
    reminder_sent = fields.Boolean(string="Recordatorio enviado", default=False)

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
                record.reminder_sent = True
            else:
                _logger.info(f"No se envió recordatorio a {persona.nombre}: enviar_email={persona.enviar_email}, email={persona.email}")

    def _send_reminders(self):
        now = fields.Datetime.now()
        target_time = now + timedelta(hours=24)

        citas = self.search([
            ('fecha', '>=', target_time - timedelta(minutes=5)),
            ('fecha', '<=', target_time + timedelta(minutes=5)),
            ('reminder_sent', '=', False)
        ])

        for cita in citas:
            if cita.persona_id.email:
                template = self.env.ref('mi_modulo.mail_template_recordatorio')
                template.send_mail(cita.id, force_send=True)
                cita.reminder_sent = True
    

