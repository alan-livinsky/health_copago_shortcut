import datetime

from trytond.exceptions import UserError
from trytond.modules.health.core import get_institution
from trytond.pyson import PYSONEncoder
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import StateAction, StateReport, Wizard


class OpenAppointmentCopagoServices(Wizard):
    'Open Appointment Copago Services'
    __name__ = 'wizard.gnuhealth.appointment.copago.services'

    start_state = 'open_'
    open_ = StateAction('health_copago_shortcut.act_copago_patient_services')

    def do_open_(self, action):
        appointment = self._get_appointment()
        patient = self._get_patient(appointment)

        action['pyson_domain'] = PYSONEncoder().encode([
            ('patient', '=', patient.id),
        ])
        action['pyson_context'] = PYSONEncoder().encode({
            'patient': patient.id,
        })
        action['name'] += ' - %s' % patient.rec_name
        return action, {}

    @staticmethod
    def _get_appointment():
        pool = Pool()
        Appointment = pool.get('gnuhealth.appointment')

        active_ids = Transaction().context.get('active_ids') or []
        if len(active_ids) != 1:
            raise UserError('Select exactly one appointment.')
        return Appointment(active_ids[0])

    @staticmethod
    def _get_patient(appointment):
        if not appointment.patient:
            raise UserError('The selected appointment does not have a patient.')
        return appointment.patient


class GenerateAppointmentCopago(Wizard):
    'Generate Appointment Copago'
    __name__ = 'wizard.gnuhealth.appointment.copago.generate'

    start_state = 'open_invoice'
    open_invoice = StateAction('health_copago_shortcut.act_copago_invoice')

    def do_open_invoice(self, action):
        service, invoice = self._generate_copago()

        action['res_id'] = invoice.id
        action['pyson_domain'] = PYSONEncoder().encode([
            ('id', '=', invoice.id),
        ])
        action['pyson_context'] = PYSONEncoder().encode({
            'active_id': invoice.id,
            'active_ids': [invoice.id],
            'active_model': 'account.invoice',
        })
        action['name'] += ' - %s' % service.name
        return action, {}

    def _generate_copago(self):
        pool = Pool()
        HealthService = pool.get('gnuhealth.health_service')
        Product = pool.get('product.product')

        appointment = OpenAppointmentCopagoServices._get_appointment()
        patient = OpenAppointmentCopagoServices._get_patient(appointment)
        product = self._get_copago_product(Product)
        today = datetime.date.today()
        company_id = Transaction().context.get('company')
        if not company_id:
            raise UserError('No default company is available in the current context.')

        service, = HealthService.create([{
            'patient': patient.id,
            'desc': 'copago',
            'institution': get_institution(),
            'company': company_id,
            'service_date': today,
            'invoice_to': patient.name.id,
            'service_line': [('create', [{
                'product': product.id,
                'desc': getattr(product, 'name', None) or product.rec_name,
                'qty': 1,
                'from_date': today,
                'to_date': today,
                'to_invoice': True,
            }])],
        }])

        invoice = self._create_invoice(service)
        return service, invoice

    @staticmethod
    def _get_copago_product(Product):
        searches = [
            '[md-1]%',
            'md-1%',
            '%md-1%',
        ]
        for term in searches:
            products = Product.search([
                ('rec_name', 'ilike', term),
            ], limit=1)
            if products:
                return products[0]
        raise UserError(
            'Could not find the copago product. Expected something matching md-1.'
        )

    @staticmethod
    def _create_invoice(service):
        pool = Pool()
        HealthService = pool.get('gnuhealth.health_service')
        Invoice = pool.get('account.invoice')
        Party = pool.get('party.party')
        Journal = pool.get('account.journal')
        AcctConfig = pool.get('account.configuration')
        acct_config = AcctConfig(1)

        currency_id = Transaction().context.get('currency')
        party = service.invoice_to or service.patient.name
        invoice_data = {
            'description': service.desc,
            'party': party.id,
            'type': 'out',
            'invoice_date': datetime.date.today(),
            'company': service.company.id if service.company else None,
            'reference': service.name,
        }

        if party.account_receivable:
            invoice_data['account'] = party.account_receivable.id
        elif acct_config.default_account_receivable:
            invoice_data['account'] = acct_config.default_account_receivable.id
        else:
            raise UserError('No receivable account is configured for this party.')

        sale_price_list = getattr(party, 'sale_price_list', None)
        ctx = {}
        if sale_price_list:
            ctx = {
                'price_list': sale_price_list.id,
                'sale_date': datetime.date.today(),
                'currency': currency_id,
                'customer': party.id,
            }

        journals = Journal.search([
            ('type', '=', 'revenue'),
        ], limit=1)
        if not journals:
            raise UserError('No revenue journal is configured.')
        invoice_data['journal'] = journals[0].id

        party_address = Party.address_get(party, type='invoice')
        if not party_address:
            raise UserError('The invoiced party does not have an invoice address.')
        invoice_data['invoice_address'] = party_address.id

        if party.customer_payment_term:
            invoice_data['payment_term'] = party.customer_payment_term.id
        elif acct_config.default_customer_payment_term:
            invoice_data['payment_term'] = (
                acct_config.default_customer_payment_term.id)
        else:
            raise UserError('No customer payment term is configured.')

        invoice_lines = []
        sequence = 0
        for line in service.service_line:
            if not line.to_invoice:
                continue
            sequence += 1
            account = line.product.template.account_revenue_used
            if not account:
                raise UserError(
                    'The copago product does not have a revenue account.')

            if sale_price_list:
                with Transaction().set_context(ctx):
                    unit_price = sale_price_list.compute(
                        party,
                        line.product,
                        line.product.list_price,
                        line.qty,
                        line.product.default_uom)
            else:
                unit_price = line.product.list_price

            taxes = [tax.id for tax in line.product.customer_taxes_used]
            invoice_lines.append(('create', [{
                'origin': str(line),
                'product': line.product.id,
                'description': line.desc,
                'quantity': line.qty,
                'account': account.id,
                'unit': line.product.default_uom.id,
                'unit_price': unit_price,
                'sequence': sequence,
                'taxes': [('add', taxes)],
            }]))

        if not invoice_lines:
            raise UserError('The generated service does not contain invoiceable lines.')

        invoice_data['lines'] = invoice_lines
        invoice, = Invoice.create([invoice_data])
        Invoice.update_taxes([invoice])
        HealthService.write([service], {'state': 'invoiced'})
        return invoice


class GenerateAppointmentCopagoPrint(GenerateAppointmentCopago):
    'Generate Appointment Copago Print'
    __name__ = 'wizard.gnuhealth.appointment.copago.print'

    start_state = 'print_'
    print_ = StateReport('account.invoice')

    def do_print_(self, action):
        service, invoice = self._generate_copago()
        data = {
            'id': invoice.id,
            'ids': [invoice.id],
            'model': 'account.invoice',
        }
        return action, data
