# -*- coding: utf-8 -*-
# from odoo import http

# class MotorcycleDealerManager(http.Controller):
#     @http.route('/motorcycle_dealer_manager/motorcycle_dealer_manager', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/motorcycle_dealer_manager/motorcycle_dealer_manager/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('motorcycle_dealer_manager.listing', {
#             'root': '/motorcycle_dealer_manager/motorcycle_dealer_manager',
#             'objects': http.request.env['motorcycle_dealer_manager.motorcycle_dealer_manager'].search([]),
#         })

#     @http.route('/motorcycle_dealer_manager/motorcycle_dealer_manager/objects/<model("motorcycle_dealer_manager.motorcycle_dealer_manager"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('motorcycle_dealer_manager.object', {
#             'object': obj
#         })
