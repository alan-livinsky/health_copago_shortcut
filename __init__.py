from trytond.pool import Pool

from . import report
from . import wizard


def register():
    Pool.register(
        wizard.OpenAppointmentCopagoServices,
        wizard.GenerateAppointmentCopago,
        wizard.GenerateAppointmentCopagoPrint,
        module='health_copago_shortcut', type_='wizard')
    Pool.register(
        report.invoice.InvoiceReport,
        module='health_copago_shortcut', type_='report')
