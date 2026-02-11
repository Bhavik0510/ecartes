# -*- coding: utf-8 -*-
# from odoo import http


# class ProductWarranty(http.Controller):
#     @http.route('/product_warranty/product_warranty', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_warranty/product_warranty/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_warranty.listing', {
#             'root': '/product_warranty/product_warranty',
#             'objects': http.request.env['product_warranty.product_warranty'].search([]),
#         })

#     @http.route('/product_warranty/product_warranty/objects/<model("product_warranty.product_warranty"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_warranty.object', {
#             'object': obj
#         })
