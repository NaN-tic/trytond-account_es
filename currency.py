# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import ROUND_HALF_UP
from trytond.pool import PoolMeta
from trytond.exceptions import UserError
from trytond.i18n import gettext

__all__ = ['Currency']


class Currency(metaclass=PoolMeta):
    __name__ = 'currency.currency'

    def round(self, amount, rounding=ROUND_HALF_UP):
        if amount is None:
            raise UserError(gettext('account_es.currency_amount_needed'))
        return super(Currency, self).round(amount, rounding=rounding)
