from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError



class AmcClaim(models.Model):
    _name = 'amc.claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'claim_description'
    _description = 'Amc Claim'

    claim_description = fields.Char(string="Claim Description", required=True)
    claim_date = fields.Date(string="Claim Date", required=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, check_company=True,readonly=True)
    deadline_date = fields.Date(string="Deadline Date")
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True,
        default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, check_company=True, change_default=True)
    priority = fields.Selection([('0', 'Normal'),('1', 'Low'), ('2', 'Urgent'), ('3', 'Very High')], default='0', string="Priority")

    state = fields.Selection(string="Status", selection=[('new', 'New'), ('under_maintenance', 'Under Maintenance'),('ready_to_deliver','Ready To Deliver'),('done','Done') ], default="new")

    amc_id = fields.Many2one('amc.amc',string="AMC")
    
    state = fields.Selection(string="Status", selection=[('new', 'New'), ('confirm', 'Confirm'), ('under_maintenance', 'Under Maintenance'),
                                                         ('ready_to_deliver', 'Ready To Deliver'), ('done', 'Done')],
                             default="new")

    amc_line_ids = fields.One2many(comodel_name="amc.line", inverse_name="amc_claim_id")
   
    def under_maintenance(self):
        self.state = 'under_maintenance'

    def ready_to_deliver(self):
        self.state = 'ready_to_deliver'

    def done(self):
        self.state = 'done'

    def confirm_claim(self):
        if self.amc_id.state == 'expired' and not self.env.user.has_group('ecartes_amc.allow_claim_forcefully'):
            raise ValidationError('Your amc is expired ')
        else:
            self.state = 'confirm'    
