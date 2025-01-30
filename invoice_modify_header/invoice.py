import hashlib
from trytond.pool import Pool, PoolMeta
from trytond.model import Model, ModelView
from trytond.pyson import Eval
from trytond.wizard import Button, StateTransition, StateView, Wizard
from trytond.model.exceptions import AccessError
from trytond.i18n import gettext
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # readonly party in case has lines
        _READONLY = (cls.party.states['readonly']
            | (Eval('lines', [0]) & Eval('party')))
        cls.party.states['readonly'] = _READONLY

        cls._buttons.update({
                'modify_header': {
                    'invisible': ((Eval('state') != 'draft')
                        | ~Eval('lines', [-1])),
                    'depends': ['state'],
                    },
                })

    @classmethod
    def view_attributes(cls):
        attributes = super().view_attributes()
        if Transaction().context.get('modify_header'):
            attributes.extend([
                    ('//group[@id="states"]', 'states', {'invisible': True}),
                    ('//group[@id="taxes_amount_state"]', 'states', {'invisible': True}),
                    ('//group[@id="links"]', 'states', {'invisible': True}),
                    ('//group[@id="buttons"]', 'states', {'invisible': True}),
                    ])
        return attributes

    @classmethod
    @ModelView.button_action('account_es.wizard_modify_header')
    def modify_header(cls, invoices):
        pass


class ModifyHeaderStateView(StateView):
    def get_view(self, wizard, state_name):
        with Transaction().set_context(modify_header=True):
            return super(ModifyHeaderStateView, self).get_view(
                wizard, state_name)

    def get_defaults(self, wizard, state_name, fields):
        return {}


class ModifyHeader(Wizard):
    "Modify Header"
    __name__ = 'invoice.modify_header'
    start = ModifyHeaderStateView('account.invoice',
        'account_es.modify_header_form', [
            Button("Cancel", 'end', 'tryton-cancel'),
            Button("Modify", 'modify', 'tryton-ok', default=True),
            ])
    modify = StateTransition()

    def get_invoice(self):
        if self.record.state != 'draft':
            raise AccessError(
                gettext('account_es.msg_invoice_modify_header_draft',
                    invoice=self.record.rec_name))
        return self.record

    def value_start(self, fields):
        invoice = self.get_invoice()
        values = {}
        for fieldname in fields:
            value = getattr(invoice, fieldname)
            if isinstance(value, Model):
                if getattr(invoice.__class__, fieldname)._type == 'reference':
                    value = str(value)
                else:
                    value = value.id
            elif isinstance(value, (list, tuple)):
                value = [r.id for r in value]
            values[fieldname] = value

        # Mimic an empty invoice in draft state to get the fields' states right
        values['lines'] = []
        return values

    def transition_modify(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Line = pool.get('account.invoice.line')
        Warning = pool.get('res.user.warning')

        invoice = self.get_invoice()
        values = self.start._save_values

        digest = hashlib.sha1(str(values).encode('utf-8')).hexdigest()
        warning_name = 'modify_invoice_header_%s_%s' % (invoice.id, digest)
        if Warning.check(warning_name):
            raise UserWarning(warning_name,
                gettext('account_es.msg_invoice_modify_header_alert',
                    invoice=invoice.rec_name))

        party_id = values.get('party')
        # before save invoice, sure that the party line is the same
        line_ids = []
        for line in invoice.lines:
            if line.party and line.party.id != party_id:
                line_ids.append(line.id)
        if line_ids:
            table = Line.__table__()
            cursor = Transaction().connection.cursor()
            cursor.execute(*table.update(
                    columns=[table.party],
                    values=[party_id],
                    where=table.id.in_(line_ids)))
            invoice = Invoice(invoice.id)

        self.model.write([invoice], values)
        self.model.log([invoice], 'write', ','.join(sorted(values.keys())))

        # Call on_change after the save to ensure parent invoice
        # has the modified values
        for line in invoice.lines:
            line.on_change_product()
        Line.save(invoice.lines)

        return 'end'
