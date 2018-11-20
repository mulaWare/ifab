from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class Project(models.Model):
    _inherit = 'project.project'

    description = fields.Char("Description", default=False, help="Description of the project")
    contract = fields.Char("Contract", default=False, help="Contract of the project")
    study = fields.Char("Study", default=False, help="Study of the project")
    sample = fields.Integer("Sample", default=False, help="Size of the sample of the project")
    date_sign = field.Date("Signature", default=False, help="Signature date of the contract")
    code = fields.Char('Order Reference', required=True, index=True, copy=False, default='New')
