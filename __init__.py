#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from .account import *
from .currency import *


def register():
    Pool.register(
        Currency,
        Account,
        TaxTemplate,
        Tax,
        module='account_es', type_='model')

