import base64
import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        result = super().write(vals)
        self._maybe_sync_to_nextcloud()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._maybe_sync_to_nextcloud()
        return orders

    def _maybe_sync_to_nextcloud(self):
        if self.env['ir.config_parameter'].sudo().get_param(
            'vendor_bill_stamp.out_quote_enabled', 'False'
        ) != 'True':
            return
        for order in self:
            try:
                order._stamp_and_sync_sale()
            except Exception as e:
                _logger.error("vendor_bill_stamp: erreur devis %s : %s", order.name, e, exc_info=True)

    def _stamp_and_sync_sale(self):
        get = self.env['ir.config_parameter'].sudo().get_param
        apply_stamp = get('vendor_bill_stamp.out_quote_stamp', 'False') == 'True'

        _logger.info("vendor_bill_stamp: traitement devis %s (tampon: %s)", self.name, apply_stamp)

        report = self.env.ref('sale.action_report_saleorder')
        pdf_bytes, _ = report._render_qweb_pdf('sale.action_report_saleorder', self.ids)

        if apply_stamp:
            show_number = get('vendor_bill_stamp.show_number', 'True') == 'True'
            show_ref    = get('vendor_bill_stamp.show_ref',    'False') == 'True'
            separator   = get('vendor_bill_stamp.separator',   ' | ')

            parts = []
            if show_number and self.name:
                parts.append(self.name)
            if show_ref and self.client_order_ref:
                parts.append(self.client_order_ref)
            stamp_text = separator.join(parts) if parts else (self.name or '')

            if stamp_text:
                from odoo.addons.vendor_bill_stamp.models.account_move import AccountMove
                final_b64 = AccountMove._apply_stamp_to_pdf(
                    pdf_bytes,
                    stamp_text,
                    get('vendor_bill_stamp.text_color',  '#1A56DB'),
                    int(get('vendor_bill_stamp.font_size', '11')),
                    get('vendor_bill_stamp.position_v',  'top'),
                    get('vendor_bill_stamp.position_h',  'right'),
                )
            else:
                final_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        else:
            final_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        if get('vendor_bill_stamp.nc_enabled', 'False') == 'True':
            nc_path_tpl = get('vendor_bill_stamp.nc_path_out_quote', '/Devis/{year}/')
            self._sync_sale_to_nextcloud(final_b64, nc_path_tpl)

    def _sync_sale_to_nextcloud(self, pdf_b64, nc_path_tpl):
        import requests
        from odoo.addons.vendor_bill_stamp.models.account_move_nextcloud import AccountMoveNextcloud

        get = self.env['ir.config_parameter'].sudo().get_param
        nc_url      = (get('vendor_bill_stamp.nc_url')     or '').rstrip('/')
        nc_user     = get('vendor_bill_stamp.nc_user')     or ''
        nc_password = get('vendor_bill_stamp.nc_password') or ''

        if not nc_url or not nc_user or not nc_password:
            _logger.warning("vendor_bill_stamp: Nextcloud non configuré, sync devis ignoré.")
            return

        order_date = self.date_order or self.create_date
        variables = {
            'year':   order_date.strftime('%Y') if order_date else 'inconnu',
            'month':  order_date.strftime('%m') if order_date else '00',
            'day':    order_date.strftime('%d') if order_date else '00',
            'ref':    re.sub(r'[\\/*?:"<>|]', '_', self.client_order_ref or '').strip(),
            'number': re.sub(r'[\\/*?:"<>|]', '_', self.name or '').strip(),
        }

        try:
            nc_path = nc_path_tpl.strip().format(**variables).rstrip('/') + '/'
        except KeyError as e:
            _logger.error("vendor_bill_stamp: variable inconnue chemin devis : %s", e)
            return

        filename = re.sub(r'[\\/*?:"<>|]', '_', self.name or 'devis').strip() + '.pdf'
        auth = (nc_user, nc_password)
        webdav_base = f"{nc_url}/remote.php/dav/files/{nc_user}"

        AccountMoveNextcloud._nextcloud_mkdirp(webdav_base, nc_path, auth)

        resp = requests.put(
            f"{webdav_base}{nc_path}{filename}",
            data=base64.b64decode(pdf_b64),
            auth=auth,
            headers={'Content-Type': 'application/pdf'},
            timeout=30,
        )
        if resp.status_code in (200, 201, 204):
            _logger.info("vendor_bill_stamp: devis %s envoyé → %s%s", self.name, nc_path, filename)
        else:
            _logger.error("vendor_bill_stamp: erreur Nextcloud devis %s : %s", self.name, resp.status_code)
