#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from .account import *


def register():
    Pool.register(
        Account,
        TaxTemplate,
        Tax,
        module='account_es', type_='model')

