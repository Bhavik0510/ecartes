# -*- coding: utf-8 -*-


import pytz
from datetime import datetime, date
from collections import OrderedDict
from psycopg2 import sql

from odoo import models, fields, api, tools, _, SUPERUSER_ID
from odoo.addons.crm.models import crm_stage


class TenderTag(models.Model):
    _name = 'tender.tag'
    _description = 'Tender Tag'

    name = fields.Char(string="Tender Mode", required=True)


class TenderPipeline(models.Model):
    _name = 'tender.pipeline'
    _description = 'Tender Pipeline'
    _order = "priority desc, id desc"
    _inherit = ['mail.thread.cc',
                'mail.thread.blacklist',
                'mail.thread.phone',
                'mail.activity.mixin',
                'utm.mixin',
                'format.address.mixin',
               ]
    _primary_email = 'email_from'
    _check_company_auto = True

    name = fields.Char(
        'Tender Name', index=True, required=True,
        compute='_compute_name', readonly=False, store=True)
    user_id = fields.Many2one(
        'res.users', string='Sales Person', default=lambda self: self.env.user,
        domain="['&', ('share', '=', False), ('company_ids', 'in', user_company_ids)]",
        check_company=True, index=True, tracking=True)
    user_company_ids = fields.Many2many(
        'res.company', compute='_compute_user_company_ids',
        help='UX: Limit to tender company or all if no company')
    user_email = fields.Char('User Email', related='user_id.email', readonly=True)
    user_login = fields.Char('User Login', related='user_id.login', readonly=True)
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', check_company=True, index=True, tracking=True,
        domain="[('is_tender_team', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        compute='_compute_team_id', ondelete="set null", readonly=False, store=True)
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        compute='_compute_company_id', readonly=False, store=True)
    currency_id = fields.Many2one('res.currency', string="Currency", store=True, ondelete="restrict")

    reference = fields.Char(string="Tender Reference", required=True)
    tender_date = fields.Date(string="Tender Date", required=True)
    tender_id = fields.Char(string="Tender Id", required=True)
    tender_mode = fields.Many2one("tender.tag", string="Tender Mode", required=True)
    publish_date = fields.Date(string="Publish Date", required=True)
    submission_date = fields.Datetime(string="Submission Date", required=True)
    opening_date = fields.Datetime(string="Opening Date", required=True)
    last_date = fields.Date(string="Last date for Submitting Queries", required=False)
    pre_bid_meeting = fields.Datetime(string="Pre-Bid Meeting Date", required=True)
    pre_bid_venue = fields.Text(string="Pre-Bid Meeting Venue & Contact", required=False)

    tender_value = fields.Float(string="Tender Value", required=True)
    transaction_fee = fields.Float(string="Transaction Fee", required=True)
    tender_fee = fields.Float(string="Tender Fee", required=True)
    tender_fee_exempt = fields.Boolean(string="Tender Fee Exempt")
    emd = fields.Float(string="EMD")
    emd_exempt = fields.Boolean(string="EMD Exempt")
    maf_required = fields.Boolean(string="MAF required")
    important_points = fields.Text(string="Important Points", required=True)

    qualified_companies = fields.Text(string="Qualified Companies")
    financial_result = fields.Text(string="Financial Result")
    winning_amount = fields.Float(string="Winning Amount")
    lost_reason = fields.Many2one("crm.lost.reason", string="Reason for Loss")

    #might not require in future
    po_received = fields.Boolean(string="PO Received")
    financial_attachments = fields.One2many('ir.attachment', 'res_id', string="Financial Result(s)")

    emd_status = fields.Selection([('not_selected', 'Not Selected'), 
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default="not_selected",
        string="EMD status")
    emd_returned = fields.Boolean(string="EMD Returned")
    emd_issue = fields.Boolean(string="EMD Issue")

    pbg_status = fields.Selection([('not_selected', 'Not Selected'), 
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default="not_selected",
        string="PBG status")
    pbg_returned = fields.Boolean(string="PBG Returned")
    pbg_issue = fields.Boolean(string="PBG Issue")

    active = fields.Boolean('Active', default=True, tracking=True)

    priority = fields.Selection(
        crm_stage.AVAILABLE_PRIORITIES, string='Priority', index=True,
        default=crm_stage.AVAILABLE_PRIORITIES[0][0])
    stage_id = fields.Many2one(
        'crm.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
        domain="[('is_tender_stage', '=', True), '|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    is_qualified_stage = fields.Boolean(related="stage_id.is_qualified_stage", string="Is Qualified Stage?")
    is_financial_stage = fields.Boolean(related="stage_id.is_financial_stage", string="Is Financial Stage?")
    is_won_stage = fields.Boolean(related="stage_id.is_won", string="Is Won?")
    kanban_state = fields.Selection([
        ('grey', 'No next activity planned'),
        ('red', 'Next activity late'),
        ('green', 'Next activity is planned')], string='Kanban State',
        compute='_compute_kanban_state')
    color = fields.Integer('Color Index', default=0)

    company_currency = fields.Many2one("res.currency", string='Company Currency', compute="_compute_company_currency", readonly=True)

    email_from = fields.Char(
        'Email', tracking=40, index=True,
        compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', check_company=True, index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the tender. You can find a partner by its Name, TIN, Email or Internal Reference.")

    calendar_event_ids = fields.One2many('calendar.event', 'tp_id', string='Meetings')
    calendar_event_count = fields.Integer('# Meetings', compute='_compute_calendar_event_count')

    sale_amount_total = fields.Monetary(compute='_compute_sale_data', string="Sum of Orders", help="Untaxed Total of Confirmed Orders", currency_field='company_currency')
    quotation_count = fields.Integer(compute='_compute_sale_data', string="Number of Quotations")
    sale_order_count = fields.Integer(compute='_compute_sale_data', string="Number of Sale Orders")
    order_ids = fields.One2many('sale.order', 'tender_pipeline_id', string='Orders')

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent'):
                    quotation_cnt += 1
                if order.state not in ('draft', 'sent', 'cancel'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt

    lang_id = fields.Many2one(
        'res.lang', string='Language',
        compute='_compute_lang_id', readonly=False, store=True)

    @api.depends('partner_id')
    def _compute_lang_id(self):
        """ compute the lang based on partner, erase any value to force the partner
        one if set. """
        # prepare cache
        lang_codes = [code for code in self.mapped('partner_id.lang') if code]
        if lang_codes:
            lang_id_by_code = dict(
                (code, self.env['res.lang']._get_data(code=code).id)
                for code in lang_codes
            )
        else:
            lang_id_by_code = {}
        for lead in self.filtered('partner_id'):
            lead.lang_id = lang_id_by_code.get(lead.partner_id.lang, False)

    def _compute_calendar_event_count(self):
        if self.ids:
            meeting_data = self.env['calendar.event'].sudo().read_group([
                ('tp_id', 'in', self.ids)
            ], ['tp_id'], ['tp_id'])
            mapped_data = {m['tp_id'][0]: m['tp_id_count'] for m in meeting_data}
        else:
            mapped_data = dict()
        for tender in self:
            tender.calendar_event_count = mapped_data.get(tender.id, 0)

    @api.depends('company_id')
    def _compute_company_currency(self):
        for tender in self:
            if not tender.company_id:
                tender.company_currency = self.env.company.currency_id
            else:
                tender.company_currency = tender.company_id.currency_id

    @api.depends('partner_id.email')
    def _compute_email_from(self):
        for tender in self:
            if tender.partner_id.email and tender._get_partner_email_update():
                tender.email_from = tender.partner_id.email

    def _inverse_email_from(self):
        for tender in self:
            if tender._get_partner_email_update():
                tender.partner_id.email = tender.email_from

    def _get_partner_email_update(self):
        self.ensure_one()
        if self.partner_id and self.email_from != self.partner_id.email:
            tender_email_normalized = tools.email_normalize(self.email_from) or self.email_from or False
            partner_email_normalized = tools.email_normalize(self.partner_id.email) or self.partner_id.email or False
            return tender_email_normalized != partner_email_normalized
        return False

    @api.depends('activity_date_deadline')
    def _compute_kanban_state(self):
        today = date.today()
        for tender in self:
            kanban_state = 'grey'
            if tender.activity_date_deadline:
                tender_date = fields.Date.from_string(tender.activity_date_deadline)
                if tender_date >= today:
                    kanban_state = 'green'
                else:
                    kanban_state = 'red'
            tender.kanban_state = kanban_state

    @api.depends('partner_id')
    def _compute_name(self):
        for tender in self:
            if not tender.name and tender.partner_id and tender.partner_id.name:
                tender.name = _("%s's Tender") % tender.partner_id.name

    @api.depends('company_id')
    def _compute_user_company_ids(self):
        all_companies = self.env['res.company'].search([])
        for tender in self:
            if not tender.company_id:
                tender.user_company_ids = all_companies
            else:
                tender.user_company_ids = tender.company_id

    @api.depends('user_id')
    def _compute_team_id(self):
        for tender in self:
            if not tender.user_id:
                continue
            user = tender.user_id
            if tender.team_id and user in (tender.team_id.member_ids | tender.team_id.user_id):
                continue
            team_domain = [('is_tender_team', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            tender.team_id = team.id

    @api.depends('user_id', 'team_id', 'partner_id')
    def _compute_company_id(self):
        """ Compute company_id coherency. """
        for tender in self:
            proposal = tender.company_id

            # invalidate wrong configuration
            if proposal:
                # company not in responsible companies
                if tender.user_id and proposal not in tender.user_id.company_ids:
                    proposal = False
                # inconsistent
                if tender.team_id.company_id and proposal != tender.team_id.company_id:
                    proposal = False
                # void company on team and no assignee
                if tender.team_id and not tender.team_id.company_id and not tender.user_id:
                    proposal = False
                # no user and no team -> void company and let assignment do its job
                # unless customer has a company
                if not tender.team_id and not tender.user_id and \
                   (not tender.partner_id or tender.partner_id.company_id != proposal):
                    proposal = False

            # propose a new company based on team > user (respecting context) > partner
            if not proposal:
                if tender.team_id.company_id:
                    proposal = tender.team_id.company_id
                elif tender.user_id:
                    if self.env.company in tender.user_id.company_ids:
                        proposal = self.env.company
                    else:
                        proposal = tender.user_id.company_id & self.env.companies
                elif tender.partner_id:
                    proposal = tender.partner_id.company_id
                else:
                    proposal = False

            # set a new company
            if tender.company_id != proposal:
                tender.company_id = proposal

    @api.depends('team_id')
    def _compute_stage_id(self):
        for tender in self:
            if not tender.stage_id:
                tender.stage_id = tender._stage_find(domain=[('is_tender_stage', '=', True), ('fold', '=', False)]).id

    def _stage_find(self, team_id=False, domain=None, order='sequence, id', limit=1):
        team_ids = set()
        if team_id:
            team_ids.add(team_id)
        for tender in self:
            if tender.team_id:
                team_ids.add(tender.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['crm.stage'].search(search_domain, order=order, limit=limit)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        team_id = self._context.get('default_team_id')
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = [('is_tender_stage', '=', True), '|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = [('is_tender_stage', '=', True), '|', ('id', 'in', stages.ids), ('team_id', '=', False)]
        stage_ids = stages._search(search_domain, order=stages._order)
        return stages.browse(stage_ids)

    def action_set_won(self):
        """ Won semantic: probability = 100 (active untouched) """
        self.action_unarchive()
        # group the leads by team_id, in order to write once by values couple (each write leads to frequency increment)
        tenders_by_won_stage = {}
        for tender in self:
            won_stages = self._stage_find(domain=[('is_tender_stage', '=', True), ('is_won', '=', True)], limit=None)
            stage_id = next((stage for stage in won_stages if stage.sequence > tender.stage_id.sequence), None)
            if not stage_id:
                stage_id = next((stage for stage in reversed(won_stages) if stage.sequence <= tender.stage_id.sequence), won_stages)
            if stage_id in tenders_by_won_stage:
                tenders_by_won_stage[stage_id] += tender
            else:
                tenders_by_won_stage[stage_id] = tender
        for won_stage_id, tenders in tenders_by_won_stage.items():
            tenders.write({'stage_id': won_stage_id.id})
        return True

    def toggle_active(self):
        activated = self.filtered(lambda tender: tender.active)
        if activated:
            activated.write({'lost_reason': False})
        return True

    def action_set_lost(self, **additional_values):
        res = self.action_archive()
        if additional_values:
            self.write(dict(additional_values))
        return res

    def _get_rainbowman_message(self):
        if not self.user_id or not self.team_id:
            return False
        self.flush()  # flush fields to make sure DB is up to date
        return _('Go, go, go! Congrats for your deal.')

    def action_set_won_rainbowman(self):
        self.ensure_one()
        self.action_set_won()

        message = self._get_rainbowman_message()
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        return True

    def action_schedule_meeting(self, smart_calendar=True):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        current_tender_id = self.id
        action['context'] = {
            'search_default_tender_pipeline_id': current_tender_id,
            'default_tp_id': current_tender_id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_team_id': self.team_id.id,
            'default_name': self.name,
        }

        # 'Smart' calendar view : get the most relevant time period to display to the user.
        if current_tender_id and smart_calendar:
            mode, initial_date = self._get_tp_meeting_view_parameters()
            action['context'].update({'default_mode': mode, 'initial_date': initial_date})

        return action

    def _get_tp_meeting_view_parameters(self):
        self.ensure_one()
        meeting_results = self.env["calendar.event"].search_read([('tp_id', '=', self.id)], ['start', 'stop', 'allday'])
        if not meeting_results:
            return "week", False

        user_tz = self.env.user.tz or self.env.context.get('tz')
        user_pytz = pytz.timezone(user_tz) if user_tz else pytz.utc

        meeting_dts = []
        now_dt = datetime.now().astimezone(user_pytz).replace(tzinfo=None)
        for meeting in meeting_results:
            if meeting.get('allday'):
                meeting_dts.append((meeting.get('start'), meeting.get('stop')))
            else:
                meeting_dts.append((meeting.get('start').astimezone(user_pytz).replace(tzinfo=None),
                                   meeting.get('stop').astimezone(user_pytz).replace(tzinfo=None)))
        unfinished_meeting_dts = [meeting_dt for meeting_dt in meeting_dts if meeting_dt[1] >= now_dt]
        relevant_meeting_dts = unfinished_meeting_dts if unfinished_meeting_dts else meeting_dts
        relevant_meeting_count = len(relevant_meeting_dts)

        if relevant_meeting_count == 1:
            return "week", relevant_meeting_dts[0][0].date()
        else:
            # Range of meetings
            earliest_start_dt = min(relevant_meeting_dt[0] for relevant_meeting_dt in relevant_meeting_dts)
            latest_stop_dt = max(relevant_meeting_dt[1] for relevant_meeting_dt in relevant_meeting_dts)

            # The week start day depends on language. We fetch the week_start of user's language. 1 is monday.
            lang_week_start = self.env["res.lang"].search_read([('code', '=', self.env.user.lang)], ['week_start'])
            # We substract one to make week_start_index range 0-6 instead of 1-7
            week_start_index = int(lang_week_start[0].get('week_start', '1')) - 1

            # We compute the weekday of earliest_start_dt according to week_start_index. earliest_start_dt_index will be 0 if we are on the
            # first day of the week and 6 on the last. weekday() returns 0 for monday and 6 for sunday. For instance, Tuesday in UK is the
            # third day of the week, so earliest_start_dt_index is 2, and remaining_days_in_week includes tuesday, so it will be 5.
            # The first term 7 is there to avoid negative left side on the modulo, improving readability.
            earliest_start_dt_weekday = (7 + earliest_start_dt.weekday() - week_start_index) % 7
            remaining_days_in_week = 7 - earliest_start_dt_weekday

            # We compute the start of the week following the one containing the start of the first meeting.
            next_week_start_date = earliest_start_dt.date() + timedelta(days=remaining_days_in_week)

            # Latest_stop_dt must be before the start of following week. Limit is therefore set at midnight of first day, included.
            meetings_in_same_week = latest_stop_dt <= datetime(next_week_start_date.year, next_week_start_date.month, next_week_start_date.day, 0, 0, 0)

            if meetings_in_same_week:
                return "week", earliest_start_dt.date()
            else:
                return "month", earliest_start_dt.date()

    def action_sale_quotations_new(self):
        if not self.partner_id:
            return self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
        else:
            return self.action_new_quotation()

    def action_new_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
        action['context'] = {
            'search_default_tender_pipeline_id': self.id,
            'default_tender_pipeline_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id
        }
        if self.team_id:
            action['context']['default_team_id'] = self.team_id.id,
        if self.user_id:
            action['context']['default_user_id'] = self.user_id.id
        return action

    def action_view_sale_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_tender_pipeline_id': self.id
        }
        action['domain'] = [('tender_pipeline_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    def action_view_sale_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_tender_pipeline_id': self.id,
        }
        action['domain'] = [('tender_pipeline_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel'))]
        orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'sent', 'cancel'))
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

