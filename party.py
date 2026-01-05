# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.modules.party.party import TAX_IDENTIFIER_TYPES


class PartyIdentifier(metaclass=PoolMeta):
    __name__ = 'party.identifier'

    @classmethod
    def default_type(cls):
        return 'eu_vat'

    def es_country(self):
        if self.type == 'eu_vat':
            return self.code[:2]
        if self.type in {'es_cif', 'es_dni', 'es_nie', 'es_nif', 'es_vat'}:
            return 'ES'

    def es_code(self):
        if self.type == 'eu_vat':
            return self.code[2:] if self.es_country() == 'ES' else self.code
        return self.code

    def es_vat_type(self):
        if self.type not in TAX_IDENTIFIER_TYPES:
            return 'SI'
        country = self.es_country()
        if country == 'ES':
            return ''
        if country is None:
            return '06'
        return '02'
