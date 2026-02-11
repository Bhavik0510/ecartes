# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    woco_url = fields.Char(string="URL", required=True) #, default="https://ecartes.woco.co.in/webhook/Userwebhook")
    woco_accesstoken = fields.Char(string="Access Token", required=True) #, default="SFJZTUg3V1RVT0dQRUg4NE1IRlBNSUxSMjc0Q0dVU1VLTzVBMVhLRFNFMU41N0ZDNVM4TTVZT0FBU00w")
    woco_authorization = fields.Char(string="Authorization", required=True) #, default="ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SmpiMjF3WVc1NVgybGtJam94TVRSOS5fUk9EUURHR29hYXREbnNVVWc5MFVBdkxld0w3Y09mV3FsMmIzWHBrS1Fj")

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('woco.woco_url', self.woco_url)
        self.env['ir.config_parameter'].sudo().set_param('woco.woco_accesstoken', self.woco_accesstoken)
        self.env['ir.config_parameter'].sudo().set_param('woco.woco_authorization', self.woco_authorization)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['woco_url'] = self.env['ir.config_parameter'].sudo().get_param('woco.woco_url')
        res['woco_accesstoken'] = self.env['ir.config_parameter'].sudo().get_param('woco.woco_accesstoken')
        res['woco_authorization'] = self.env['ir.config_parameter'].sudo().get_param('woco.woco_authorization')
        return res
