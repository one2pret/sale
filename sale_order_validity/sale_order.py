from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.depends('validity_days', 'date_order')
    def get_validity_date(self):
        for rec in self:
            date_order = fields.Datetime.from_string(rec.date_order)
            if rec.validity_days:
                rec.validity_date = fields.Datetime.to_string(
                    date_order + relativedelta(days=rec.validity_days))

    validity_days = fields.Integer(
        'Validity Days',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help='Set days of validity for Sales Order',
    )
    validity_date = fields.Date(
        "Validity Date",
        help="Date until when quotation is valid",
        readonly=True,
        compute='get_validity_date',
    )
    date_order = fields.Datetime(copy=True)

    @api.multi
    @api.onchange('company_id')
    @api.constrains('company_id')
    def onchange_company(self):
        for rec in self:
            rec.validity_days = rec.company_id.sale_order_validity_days

    @api.onchange('validity_days')
    def onchange_validity_days(self):
        company_validity_days = self.company_id.sale_order_validity_days
        if self.validity_days > company_validity_days:
            self.validity_days = self.company_id.sale_order_validity_days
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'You can not set more validity days than the configured on'
                    ' the company (%i days).' % company_validity_days),
            }
            return {'warning': warning}

    @api.multi
    def action_confirm(self):
        self.check_validity()
        return super(sale_order, self).action_confirm()

    @api.multi
    def check_validity(self):
        if self.validity_date:
            validity_date = fields.Datetime.from_string(self.validity_date)
            now = datetime.now()
            if validity_date < now:
                raise Warning(_(
                    'You can not confirm this quoatation as it was valid until'
                    ' %s! Please Update Validity.') % (self.validity_date))

    @api.multi
    def update_date_prices_and_validity(self):
        self.date_order = fields.Datetime.now()
        self.update_prices()
        self.onchange_company()
        return True
