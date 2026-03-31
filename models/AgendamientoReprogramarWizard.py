from odoo import models, fields, api

class AgendamientoReprogramarWizard(models.TransientModel):
    _name = 'agendamiento.reprogramar.wizard'
    _description = 'Wizard para Reprogramar Cita'

    nueva_fecha = fields.Datetime(string='Nueva Fecha y Hora', required=True)
    agendamiento_id = fields.Many2one('mi.agendamiento', string='Agendamiento')

    def action_reprogramar(self):
        self.ensure_one()
        # Actualizamos la fecha en el modelo principal
        self.agendamiento_id.write({
            'fecha': self.nueva_fecha,
            'estado': 'pendiente' # Opcional: volver a pendiente si estaba confirmado
        })
        return {'type': 'ir.actions.act_window_close'}