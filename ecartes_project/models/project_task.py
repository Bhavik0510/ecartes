from odoo import models,fields ,api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # responsible_person = fields.Many2one('res.users',"Responsible Person")
    participients_ids = fields.Many2many('res.partner', string='Participants')
    observers = fields.Many2one('res.users', string='Observers')
    time_tracking = fields.Boolean('Time tracking')
    repeat_task = fields.Boolean('Repeat task')
    remind_task = fields.Date('Remind about Task')








    


