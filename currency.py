# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import ROUND_HALF_UP

from trytond.pool import PoolMeta

__all__ = ['Currency']
__metaclass__ = PoolMeta


class Currency:
    __name__ = 'currency.currency'

    def round(self, amount, rounding=ROUND_HALF_UP):
        return super(Currency, self).round(amount, rounding=rounding)
