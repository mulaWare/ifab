from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class Project(models.Model):
    _inherit = 'project.project'


    description = fields.Char("Description", default=False, help="Description of the project")
    contract = fields.Char("Contract", default=False, help="Contract of the project")
    study = fields.Char("Study", default=False, help="Study of the project")
    sample = fields.Integer("Sample", default=False, help="Size of the sample of the project")
    date_sign = fields.Date("Signature Date", default=False, help="Signature date of the contract")
    code = fields.Char(string='Reference', index=True, track_visibility='onchange', default='0000',readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('code', '0000') == '0000':
            vals['code'] = self.env['ir.sequence'].next_by_code('project.project') or '/'
        return super(Project, self).create(vals)
