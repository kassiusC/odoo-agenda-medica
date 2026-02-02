from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import timedelta
from odoo.exceptions import ValidationError

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
    fecha_fin = fields.Datetime(
        string='Finaliza', 
        compute='_compute_fecha_fin', 
        store=True, 
        readonly=True,
        help="Fecha y hora de finalización (estimada 1 hora)."
    )

    @api.depends('fecha')
    def _compute_fecha_fin(self):
        for record in self:
            if record.fecha:
                # Sumamos automáticamente 1 hora
                record.fecha_fin = record.fecha + timedelta(hours=1)
            else:
                record.fecha_fin = False

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

    @api.constrains('fecha')
    def _check_fecha_pasada(self):
        for record in self:
            # Comparamos la fecha del registro con la fecha/hora actual
            if record.fecha and record.fecha < fields.Datetime.now():
                raise ValidationError("No puedes programar un agendamiento en una fecha pasada.")
            
    # mostrar advertencia       
    @api.onchange('fecha')
    def _onchange_fecha(self):
        if self.fecha and self.fecha < fields.Datetime.now():
            return {
                'warning': {
                    'title': "Fecha inválida",
                    'message': "Ten en cuenta que estás seleccionando una fecha que ya pasó.",
                }
            }
    
    #Corroborar que no exita otro agendamiento para el mismo medico en un rango de 1 hora
    @api.constrains('medico_id', 'fecha', 'fecha_fin', 'estado')
    def _check_disponibilidad_medico(self):
        for record in self:
            if record.medico_id and record.fecha and record.fecha_fin and record.estado != 'cancelado':
                # Buscamos si existe otra cita que se solape
                colision = self.search([
                    ('id', '!=', record._origin.id),
                    ('medico_id', '=', record.medico_id.id),
                    ('estado', '!=', 'cancelado'),
                    ('fecha', '<', record.fecha_fin),    # Inicio de la existente antes del fin de la nueva
                    ('fecha_fin', '>', record.fecha)     # Fin de la existente después del inicio de la nueva
                ])
                
                if colision:
                    raise ValidationError("El médico ya tiene una cita en ese rango de tiempo.")