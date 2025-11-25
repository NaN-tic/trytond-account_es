# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, fields, ModelSQL
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.modules.account_payment.payment import KINDS


class Journal(metaclass=PoolMeta):
    __name__ = 'account.payment.journal'
    require_bank_account = fields.Boolean('Require bank account',
        help=('If your bank allows you to send payment groups without the bank'
            ' account info, you may disable this option.'))
    suffix = fields.Char('Suffix', states={
            'required': Eval('process_method') != 'none'
            })
    ine_code = fields.Char('INE code')

    @staticmethod
    def default_suffix():
        return '000'


class AccountBankJournal(metaclass=PoolMeta):
    __name__ = 'account.payment.journal'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.party.states.update({
                'required': ~Eval('process_method').in_(['manual', 'sepa']),
                })


class Group(metaclass=PoolMeta):
    __name__ = 'account.payment.group'
    planned_date = fields.Date('Planned Date', readonly=True)
    process_method = fields.Function(fields.Char('Process Method'),
        'get_process_method')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('number', 'DESC'))

    def get_process_method(self, name):
        return self.journal.process_method

    def attach_file(self, data):
        IrAttachment = Pool().get('ir.attachment')
        journal = self.journal
        values = {
            'name': '%s_%s_%s' % (gettext('account_es.msg_payment_remittance'),
                journal.process_method, self.reference),
            'type': 'data',
            'data': data,
            'resource': '%s' % (self),
            }
        IrAttachment.create([values])


class PayLine(metaclass=PoolMeta):
    __name__ = 'account.move.line.pay'

    def get_payment(self, line, journals):
        payment = super().get_payment(line, journals)
        payment.reference = line.description
        if line.maturity_date:
            payment.date = line.maturity_date
        if line.origin:
            origin = line.origin.rec_name
            if not payment.reference:
                payment.reference = origin
            elif origin not in payment.reference:
                payment.reference = origin + ' ' + payment.reference
        return payment


class Payment(metaclass=PoolMeta):
    __name__ = 'account.payment'

    reconciliation = fields.Function(fields.Many2One(
            'account.move.reconciliation', 'Reconciliation',
            readonly=True, ondelete='SET NULL'), 'get_reconciliation',
        searcher='search_reconciliation')
    move_origin = fields.Function(
        fields.Reference("Move Origin", selection='get_move_origin'),
        'get_move_field', searcher='search_move_field')

    def get_reconciliation(self, name):
        return (self.line.reconciliation.id
            if self.line and self.line.reconciliation else None)

    @classmethod
    def search_reconciliation(cls, name, clause):
        nested = clause[0][len(name):]
        return [('line.reconciliation' + nested, *clause[1:])]

    @classmethod
    def get_move_origin(cls):
        Move = Pool().get('account.move')
        return Move.get_origin()

    def get_move_field(self, name):
        if not self.line or not self.line.move:
            return

        field = getattr(self.__class__, name)
        if name.startswith('move_'):
            name = name[5:]
        value = getattr(self.line.move, name)
        if isinstance(value, ModelSQL):
            if field._type == 'reference':
                return str(value)
            return value.id
        return value

    @classmethod
    def search_move_field(cls, name, clause):
        nested = clause[0][len(name):]
        if name.startswith('move_'):
            name = name[5:]
        return [('line.move.' + name + nested, *clause[1:])]


class ProcessPaymentStart(ModelView):
    'Process Payment'
    __name__ = 'account.payment.process.start'
    planned_date = fields.Date('Planned Date',
        help='Date when the payment entity must process the payment group.')
    process_method = fields.Char('Process Method')
    payments_amount = fields.Numeric('Payments Amount', digits=(16, 2),
        readonly=True)

    @classmethod
    def default_get(cls, fields_names, with_rec_name=True, with_default=True):
        pool = Pool()
        Payment = pool.get('account.payment')

        res = super().default_get(
            fields_names=fields_names,
            with_rec_name=with_rec_name,
            with_default=with_default)

        process_method = False
        payments_amount = Decimal(0)
        for payment in Payment.browse(Transaction().context.get('active_ids', [])):
            if not process_method:
                process_method = payment.journal.process_method
            else:
                if process_method != payment.journal.process_method:
                    raise UserError(gettext(
                        'account_es.msg_payment_different_process_method',
                            process=(payment.journal and
                                payment.journal.process_method
                                or ''),
                            payment=payment.rec_name,
                            pprocess=process_method))
            payments_amount += payment.amount
        res['process_method'] = process_method
        res['payments_amount'] = payments_amount
        return res


class ProcessPayment(metaclass=PoolMeta):
    __name__ = 'account.payment.process'
    start_state = 'start'
    start = StateView('account.payment.process.start',
        'account_es.payment_process_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Process', 'process', 'tryton-ok', default=True),
            ])

    def _group_payment_key(self, payment):
        res = list(super()._group_payment_key(payment))
        if self.start.planned_date:
            res.append(tuple(['planned_date', self.start.planned_date]))
        return tuple(res)

    def do_process(self, action):
        pool = Pool()
        Payment = pool.get('account.payment')

        payments = self.records

        if self.start.planned_date:
            for payment in payments:
                payment.date = self.start.planned_date
            Payment.save(payments)

        return super().do_process(action)


class CreatePaymentGroupStart(ModelView):
    'Create Payment Group Start'
    __name__ = 'account.move.line.create_payment_group.start'
    journal = fields.Many2One('account.payment.journal', 'Journal',
        required=True,
        domain=[
            ('company', '=', Eval('context', {}).get('company', -1)),
            ])
    planned_date = fields.Date('Planned Date',
        help='Date when the payment entity must process the payment group.')
    payments_amount = fields.Numeric('Payments Amount', digits=(16, 2),
        readonly=True)

    @classmethod
    def default_get(cls, fields_names, with_rec_name=True, with_default=True):
        pool = Pool()
        Line = pool.get('account.move.line')

        res = super().default_get(
            fields_names=fields_names,
            with_rec_name=with_rec_name,
            with_default=with_default)

        payments_amount = Decimal(0)
        for line in Line.browse(Transaction().context.get('active_ids', [])):
            if line.move.state != 'posted':
                raise UserError(gettext('account_es.msg_payment_non_posted_move',
                        line=line.rec_name,
                        move=line.move.rec_name,
                        ))
            payments_amount += line.payment_amount or Decimal(0)
        res['payments_amount'] = payments_amount
        return res


class CreatePaymentGroup(Wizard):
    'Create Payment Group'
    __name__ = 'account.move.line.create_payment_group'
    start = StateView('account.move.line.create_payment_group.start',
        'account_es.payment_create_payment_group_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('account_payment.act_payment_group_form')

    def do_create_(self, action):
        pool = Pool()
        Payment = pool.get('account.payment')
        PayLine = pool.get('account.move.line.pay', type='wizard')
        ProcessPayment = pool.get('account.payment.process', type='wizard')

        session_id, _, _ = PayLine.create()
        payline = PayLine(session_id)
        payline.start.date = self.start.planned_date
        payline.ask_journal.journal = self.start.journal
        payline.ask_journal.journals = [self.start.journal]
        action, data = payline.do_pay(action)
        PayLine.delete(session_id)
        payments = Payment.browse(data['res_id'])
        # Warn when submitting, approving or proceeding payment with reconciled line
        Payment._check_reconciled(payments)
        Payment.submit(payments)
        # allow create groups from receivable issues11190
        to_approve = [payment for payment in payments
            if payment.kind != 'receivable']
        if to_approve:
            Payment.approve(to_approve)

        with Transaction().set_context(active_id=None, active_ids=data['res_id'],
                active_model='account.payment'):
            session_id, _, _ = ProcessPayment.create()
            processpayment = ProcessPayment(session_id)
            processpayment.start.planned_date = self.start.planned_date
            action, data = processpayment.do_process(action)
            ProcessPayment.delete(session_id)
            return action, data


class MoveLine(metaclass=PoolMeta):
    __name__ = 'account.move.line'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
                'create_payment_group': {
                    'invisible': ~Eval('payment_kind').in_(
                        list(dict(KINDS).keys())),
                    'depends': ['payment_kind'],
                    },
                })

    @classmethod
    @ModelView.button_action('account_es.act_create_payment_group_line')
    def create_payment_group(cls, lines):
        pass


class AccountPaymentClearing(metaclass=PoolMeta):
    __name__ = 'account.payment'

    @classmethod
    def _account_type_domain(cls):
        # not call super()
        # not add domain in case account.type is receivable or payable
        return ()
