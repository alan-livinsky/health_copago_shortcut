from trytond.pool import Pool

from . import appointment
from . import report
from . import wizard


def register():
    Pool.register(
        appointment.Appointment,
        module='health_copago_shortcut', type_='model')
    Pool.register(
        wizard.OpenAppointmentCopagoServices,
        wizard.GenerateAppointmentCopago,
        wizard.GenerateAppointmentCopagoPrint,
        module='health_copago_shortcut', type_='wizard')
    Pool.register(
        report.invoice.CopagoInvoiceReport,
        module='health_copago_shortcut', type_='report')
