import base64
import io
import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Mapping type → clés de paramètres
MOVE_TYPE_CONFIG = {
    'in_invoice':  {'enabled': 'vendor_bill_stamp.bill_enabled',       'stamp': 'vendor_bill_stamp.bill_stamp',       'nc_path': 'vendor_bill_stamp.nc_path_in_invoice'},
    'in_refund':   {'enabled': 'vendor_bill_stamp.refund_enabled',      'stamp': 'vendor_bill_stamp.refund_stamp',      'nc_path': 'vendor_bill_stamp.nc_path_in_refund'},
    'out_invoice': {'enabled': 'vendor_bill_stamp.out_invoice_enabled', 'stamp': 'vendor_bill_stamp.out_invoice_stamp', 'nc_path': 'vendor_bill_stamp.nc_path_out_invoice'},
    'out_refund':  {'enabled': 'vendor_bill_stamp.out_refund_enabled',  'stamp': 'vendor_bill_stamp.out_refund_stamp',  'nc_path': 'vendor_bill_stamp.nc_path_out_refund'},
}

# xmlid du rapport de fallback selon le type
MOVE_TYPE_REPORT = {
    'in_invoice':  'account.action_account_original_vendor_bill',
    'in_refund':   'account.action_account_original_vendor_bill',
    'out_invoice': 'account.account_invoices',
    'out_refund':  'account.account_invoices',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        result = super().action_post()
        for move in self:
            try:
                move._maybe_stamp_pdf()
            except Exception as e:
                _logger.error("vendor_bill_stamp: erreur %s : %s", move.name, e, exc_info=True)
        return result

    def _maybe_stamp_pdf(self):
        cfg = MOVE_TYPE_CONFIG.get(self.move_type)
        if not cfg:
            return
        get = self.env['ir.config_parameter'].sudo().get_param
        if get(cfg['enabled'], 'False') != 'True':
            return
        apply_stamp = get(cfg['stamp'], 'True') == 'True'
        self._process_and_sync(cfg['nc_path'], apply_stamp)

    def _process_and_sync(self, nc_path_key, apply_stamp):
        get = self.env['ir.config_parameter'].sudo().get_param

        pdf_bytes, source_att = self._get_source_pdf()

        if apply_stamp:
            show_number = get('vendor_bill_stamp.show_number', 'True') == 'True'
            show_ref    = get('vendor_bill_stamp.show_ref',    'False') == 'True'
            separator   = get('vendor_bill_stamp.separator',   ' | ')
            parts = []
            if show_number and self.name:
                parts.append(self.name)
            if show_ref and self.ref:
                parts.append(self.ref)
            stamp_text = separator.join(parts) if parts else (self.name or '')

            if not stamp_text:
                return

            final_b64 = self._apply_stamp_to_pdf(
                pdf_bytes,
                stamp_text,
                get('vendor_bill_stamp.text_color',  '#1A56DB'),
                int(get('vendor_bill_stamp.font_size', '11')),
                get('vendor_bill_stamp.position_v',  'top'),
                get('vendor_bill_stamp.position_h',  'right'),
            )

            # Sauvegarder la pièce jointe estampillée
            self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', self.id),
                ('name', 'like', '_stamped.pdf'),
            ]).unlink()
            filename = "{}_stamped.pdf".format(self.name.replace('/', '_'))
            self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': final_b64,
                'res_model': 'account.move',
                'res_id': self.id,
                'mimetype': 'application/pdf',
                'description': 'PDF avec numéro apposé automatiquement',
            })
            _logger.info("vendor_bill_stamp: [%s] PDF estampillé créé (source: %s)",
                         self.name, source_att.name if source_att else 'Odoo')
        else:
            final_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            _logger.info("vendor_bill_stamp: [%s] Tampon désactivé, PDF original utilisé.", self.name)

        # Sync Nextcloud
        if get('vendor_bill_stamp.nc_enabled', 'False') == 'True':
            nc_path = get(nc_path_key, '/Documents/{year}/')
            self._sync_to_nextcloud(final_b64, nc_path)

    def _get_source_pdf(self):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf'),
            ('name', 'not like', '_stamped.pdf'),
        ], order='write_date desc')

        if len(attachments) == 1:
            att = attachments[0]
            _logger.info("vendor_bill_stamp: [%s] 1 PDF trouvé → %s", self.name, att.name)
            return base64.b64decode(att.datas), att

        if len(attachments) > 1:
            att = attachments[0]
            _logger.warning("vendor_bill_stamp: [%s] %d PDF, on prend le plus récent : %s",
                            self.name, len(attachments), att.name)
            return base64.b64decode(att.datas), att

        # Fallback : générer via Odoo avec le bon rapport selon le type
        _logger.info("vendor_bill_stamp: [%s] Aucun PDF joint, génération via Odoo.", self.name)
        report_ref = MOVE_TYPE_REPORT.get(self.move_type, 'account.action_account_original_vendor_bill')
        report = self.env.ref(report_ref)
        pdf_bytes, _ = report._render_qweb_pdf(report_ref, self.ids)
        return pdf_bytes, None

    @staticmethod
    def _apply_stamp_to_pdf(pdf_bytes, stamp_text, text_color, font_size, position_v, position_h):
        from reportlab.lib.colors import HexColor, black
        from reportlab.pdfgen import canvas
        from pypdf import PdfWriter, PdfReader

        FONT_NAME    = "Helvetica-Bold"
        STROKE_WIDTH = 0.8
        MARGIN       = 18

        try:
            fill_color = HexColor(text_color)
        except Exception:
            fill_color = HexColor('#1A56DB')

        original = PdfReader(io.BytesIO(pdf_bytes))
        output   = PdfWriter()

        for page in original.pages:
            page_w = float(page.mediabox.width)
            page_h = float(page.mediabox.height)

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(page_w, page_h))
            c.setFont(FONT_NAME, font_size)
            text_w = c.stringWidth(stamp_text, FONT_NAME, font_size)
            x = (page_w - text_w - MARGIN) if position_h == 'right' else MARGIN
            y = (page_h - font_size - MARGIN) if position_v == 'top' else MARGIN

            c.setFillColor(black)
            c.setStrokeColor(black)
            c.setLineWidth(STROKE_WIDTH)
            for dx, dy in [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]:
                c.drawString(x + dx, y + dy, stamp_text)
            c.setFillColor(fill_color)
            c.drawString(x, y, stamp_text)
            c.save()

            buf.seek(0)
            stamp_page = PdfReader(buf).pages[0]
            page.merge_page(stamp_page)
            output.add_page(page)

        out = io.BytesIO()
        output.write(out)
        return base64.b64encode(out.getvalue()).decode('utf-8')
