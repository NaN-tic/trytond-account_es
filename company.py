# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta


class Company(metaclass=PoolMeta):
    __name__ = 'company.company'

    registration_data_location = fields.Char("Register of companies location",
        translate=True, help="E.g.: Reg. M. de Barcelona")
    registration_data_book = fields.Char("Book")
    registration_data_sheet = fields.Char("Sheet")
    registration_data_folio = fields.Char("Folio")
    registration_data_section = fields.Char("Section", translate=True)
    registration_data_volume = fields.Char("Volume")
    registration_data_additional = fields.Char("Other registration data",
        translate=True)
