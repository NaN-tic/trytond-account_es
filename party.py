# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta


class PartyIdentifier(metaclass=PoolMeta):
    __name__ = 'party.identifier'

    @classmethod
    def default_type(cls):
        return 'eu_vat'

    def es_country(self):
        if self.type == 'eu_vat':
            return self.code[:2]
        if self.type in {'es_cif', 'es_dni', 'es_nie', 'es_nif'}:
            return 'ES'

    def es_code(self):
        if self.type == 'eu_vat':
            return self.code[2:11]
        if self.type in {'es_cif', 'es_dni', 'es_nie', 'es_nif'}:
            return self.code[:9]
