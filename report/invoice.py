from trytond.pool import Pool
from trytond.report import Report


class InvoiceReport(Report):
    __name__ = 'account.invoice'

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        Lang = Pool().get('ir.lang')

        def format_number_symbol(value, lang, symbol, digits=None):
            language = Lang.get(lang)
            return language.format_number_symbol(
                value, symbol, digits=digits)

        context['format_number_symbol'] = format_number_symbol
        return context
