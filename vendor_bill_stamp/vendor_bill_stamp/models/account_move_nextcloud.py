import base64
import logging
import re

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMoveNextcloud(models.Model):
    _inherit = 'account.move'

    def _sync_to_nextcloud(self, pdf_b64: str, nc_path_tpl: str):
        get = self.env['ir.config_parameter'].sudo().get_param
        nc_url      = (get('vendor_bill_stamp.nc_url')     or '').rstrip('/')
        nc_user     = get('vendor_bill_stamp.nc_user')     or ''
        nc_password = get('vendor_bill_stamp.nc_password') or ''

        if not nc_url or not nc_user or not nc_password:
            _logger.warning("vendor_bill_stamp: [%s] Nextcloud non configuré, sync ignoré.", self.name)
            return

        invoice_date = self.invoice_date or self.date
        variables = {
            'year':   invoice_date.strftime('%Y') if invoice_date else 'inconnu',
            'month':  invoice_date.strftime('%m') if invoice_date else '00',
            'day':    invoice_date.strftime('%d') if invoice_date else '00',
            'ref':    self._sanitize_filename(self.ref or ''),
            'number': self._sanitize_filename(self.name or ''),
        }

        try:
            nc_path = nc_path_tpl.strip().format(**variables).rstrip('/') + '/'
        except KeyError as e:
            _logger.error("vendor_bill_stamp: variable inconnue dans le chemin : %s", e)
            return

        filename = self._sanitize_filename(self.name or 'document') + '.pdf'

        try:
            import requests
            auth = (nc_user, nc_password)
            webdav_base = f"{nc_url}/remote.php/dav/files/{nc_user}"
            self._nextcloud_mkdirp(webdav_base, nc_path, auth)

            resp = requests.put(
                f"{webdav_base}{nc_path}{filename}",
                data=base64.b64decode(pdf_b64),
                auth=auth,
                headers={'Content-Type': 'application/pdf'},
                timeout=30,
            )
            if resp.status_code in (200, 201, 204):
                _logger.info("vendor_bill_stamp: [%s] Envoyé Nextcloud → %s%s", self.name, nc_path, filename)
            else:
                _logger.error("vendor_bill_stamp: [%s] Erreur Nextcloud %s : %s",
                              self.name, resp.status_code, resp.text[:200])
        except Exception as e:
            _logger.error("vendor_bill_stamp: [%s] Exception Nextcloud : %s", self.name, e, exc_info=True)

    @staticmethod
    def _nextcloud_mkdirp(webdav_base: str, path: str, auth: tuple):
        import requests
        parts = [p for p in path.strip('/').split('/') if p]
        current = ''
        for part in parts:
            current += '/' + part
            resp = requests.request('MKCOL', webdav_base + current, auth=auth, timeout=15)
            if resp.status_code not in (201, 405):
                _logger.warning("vendor_bill_stamp: MKCOL %s%s → %s", webdav_base, current, resp.status_code)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', '_', name).strip()
