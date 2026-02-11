# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _


class CrmLead(models.Model):
    _inherit ='crm.lead'

    company_type = fields.Many2one('vx.type.of.company', string="Type of Company",
        compute="_prepare_values_company_industry_type", readonly=False, store=True)

    industry_id = fields.Many2one("res.partner.industry", "Industry Type", compute="_prepare_values_company_industry_type", readonly=False, store=True)

    email_type = fields.Selection([('work','Work'),('home','Home'),('fornewsletters','For news letters'),
    ('other','Other')])
    phone_type = fields.Selection([('work','Work Phone'),('home','Home'),('fax','Fax'),
    ('sms_marketing','Sms Marketing'),('pager','Pager'),
    ('other','Other')])
    company_currency = fields.Many2one('res.currency','Currency')
    is_available = fields.Boolean('Available to everyone')
    state = fields.Selection([('lead_generated','Lead Generated'),('lost','Lost')], default='lead_generated',
        string="Status") #('information_obtained','Information Obtained'),
    partner_id = fields.Many2one('res.partner')
    deal_type = fields.Selection([('general_sales','General Sales'),('tenders','Tenders')])
    # responsible_id = fields.Many2one('res.users','Responsible Person')
    # type = fields.Selection(selection_add=[('tender', 'Tender')], ondelete={'tender': 'set default'})
    stage_id = fields.Many2one(
        'crm.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
        domain="[('is_tender_stage', '=', False), '|', ('team_id', '=', False), ('team_id', '=', team_id)]")

    @api.constrains('type')
    def check_team_and_type_is_tender(self):
        for tender in self:
            if tender.team_id.is_tender_team and tender.type != 'tender':
                raise ValidationError(_('You cannot create Tender Pipeline. Please contact tender team members.'))

    def action_set_lost(self):
        res = super(CrmLead, self).action_set_lost()
        self.state = 'lost'
        return res

    def toggle_active(self):
        res = super(CrmLead, self).toggle_active()
        self.state = 'lead_generated'
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(CrmLead,self).create(vals_list)
        for rec in res:
            if rec.type == 'opportunity' and rec.partner_id:
                rec.partner_id.write({
                    'type_of_company' : rec.company_type.id or False,
                    'industry_id' : rec.industry_id.id,
                    'street' : rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'zip': rec.zip,
                    'state_id': rec.state_id,
                    'country_id': rec.country_id,
                })
        return res

    @api.depends("partner_id")
    def _prepare_values_company_industry_type(self):
        for record in self:
            record.company_type = record.partner_id.type_of_company.id or False
            record.industry_id = record.partner_id.industry_id.id

    def _prepare_customer_values(self, partner_name, is_company=True, parent_id=False):
        res = super(CrmLead, self)._prepare_customer_values(partner_name, is_company=is_company,
                                                            parent_id=parent_id)
        res.update({
            'type_of_company': self.company_type.id or False,
            'industry_id': self.industry_id.id,
            'company_id': self.company_id.id or self.env.company.id or False,
            'responsible_person': self.env.context.get('default_user_id') or self.user_id.id
        })
        return res

    @api.depends('team_id', 'type')
    def _compute_stage_id(self):
        for lead in self:
            if not lead.stage_id:
                lead.stage_id = lead._stage_find(domain=[('is_tender_stage', '=', False), ('fold', '=', False)]).id

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = [('is_tender_stage', '=', False), '|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = [('is_tender_stage', '=', False), '|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=stages._order)
        return stages.browse(stage_ids)

    def write(self, vals):
        result = super(CrmLead, self).write(vals)
        stage_updated, stage_is_won = vals.get('stage_id'), False
        # stage change: update date_last_stage_update
        if stage_updated:
            stage = self.env['crm.stage'].browse(vals['stage_id'])
            if stage.is_won:
                vals.update({'probability': 100, 'automated_probability': 100})
                stage_is_won = True

        type_of_company = self.env['vx.type.of.company'].sudo().search([('is_existing_customer', '=', True)], limit=1)
        for lead in self:
            if stage_is_won and lead.partner_id and not lead.partner_id.type_of_company.is_existing_customer and\
              type_of_company:
                lead.partner_id.write({'type_of_company': type_of_company.id})
        
        return result
