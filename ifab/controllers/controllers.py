# -*- coding: utf-8 -*-
from odoo import http

# class Ifab(http.Controller):
#     @http.route('/ifab/ifab/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ifab/ifab/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ifab.listing', {
#             'root': '/ifab/ifab',
#             'objects': http.request.env['ifab.ifab'].search([]),
#         })

#     @http.route('/ifab/ifab/objects/<model("ifab.ifab"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ifab.object', {
#             'object': obj
#         })