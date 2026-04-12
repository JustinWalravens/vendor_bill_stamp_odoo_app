from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ── Tampon par type ───────────────────────────────────────────────────────
    stamp_vendor_bill_stamp = fields.Boolean(
        string='Factures fournisseurs',
        config_parameter='vendor_bill_stamp.bill_stamp',
        default=True,
    )
    stamp_vendor_refund_stamp = fields.Boolean(
        string='Notes de crédit fournisseurs',
        config_parameter='vendor_bill_stamp.refund_stamp',
        default=True,
    )
    stamp_out_invoice_stamp = fields.Boolean(
        string='Factures client',
        config_parameter='vendor_bill_stamp.out_invoice_stamp',
        default=True,
    )
    stamp_out_refund_stamp = fields.Boolean(
        string='Notes de crédit client',
        config_parameter='vendor_bill_stamp.out_refund_stamp',
        default=True,
    )
    stamp_out_quote_stamp = fields.Boolean(
        string='Devis / commandes client',
        config_parameter='vendor_bill_stamp.out_quote_stamp',
        default=False,
    )

    # ── Contenu ───────────────────────────────────────────────────────────────
    stamp_show_number = fields.Boolean(
        string='Numéro Odoo (ex: FF-26-3-21)',
        config_parameter='vendor_bill_stamp.show_number',
        default=True,
    )
    stamp_show_ref = fields.Boolean(
        string='Référence fournisseur/client',
        config_parameter='vendor_bill_stamp.show_ref',
        default=False,
    )
    stamp_separator = fields.Char(
        string='Séparateur',
        config_parameter='vendor_bill_stamp.separator',
        default=' | ',
    )

    # ── Style ─────────────────────────────────────────────────────────────────
    stamp_text_color = fields.Char(
        string='Couleur du texte',
        config_parameter='vendor_bill_stamp.text_color',
        default='#1A56DB',
        help='Code hexadécimal : #1A56DB bleu, #C0392B rouge, #000000 noir',
    )
    stamp_font_size = fields.Integer(
        string='Taille de la police (pt)',
        config_parameter='vendor_bill_stamp.font_size',
        default=11,
    )

    # ── Position ──────────────────────────────────────────────────────────────
    stamp_position_v = fields.Selection(
        selection=[('top', 'Haut'), ('bottom', 'Bas')],
        string='Position verticale',
        config_parameter='vendor_bill_stamp.position_v',
        default='top',
    )
    stamp_position_h = fields.Selection(
        selection=[('right', 'Droite'), ('left', 'Gauche')],
        string='Position horizontale',
        config_parameter='vendor_bill_stamp.position_h',
        default='right',
    )

    # ── Nextcloud — connexion ─────────────────────────────────────────────────
    stamp_nc_enabled = fields.Boolean(
        string='Activer la synchronisation Nextcloud',
        config_parameter='vendor_bill_stamp.nc_enabled',
        default=False,
    )
    stamp_nc_url = fields.Char(
        string='URL Nextcloud',
        config_parameter='vendor_bill_stamp.nc_url',
        help='Ex: https://nextcloud.mondomaine.be  (sans slash final)',
    )
    stamp_nc_user = fields.Char(
        string='Utilisateur',
        config_parameter='vendor_bill_stamp.nc_user',
    )
    stamp_nc_password = fields.Char(
        string='Mot de passe / Token',
        config_parameter='vendor_bill_stamp.nc_password',
    )

    # ── Nextcloud — activation + chemins par type ─────────────────────────────
    stamp_vendor_bill_enabled = fields.Boolean(
        string='Factures fournisseurs',
        config_parameter='vendor_bill_stamp.bill_enabled',
        default=True,
    )
    stamp_nc_path_in_invoice = fields.Char(
        string='Chemin factures fournisseurs',
        config_parameter='vendor_bill_stamp.nc_path_in_invoice',
        default='/Factures/Fournisseurs/{year}/',
        help='Variables : {year} {month} {day} {ref} {number}',
    )
    stamp_vendor_refund_enabled = fields.Boolean(
        string='Notes de crédit fournisseurs',
        config_parameter='vendor_bill_stamp.refund_enabled',
        default=False,
    )
    stamp_nc_path_in_refund = fields.Char(
        string='Chemin notes de crédit fournisseurs',
        config_parameter='vendor_bill_stamp.nc_path_in_refund',
        default='/Factures/Fournisseurs/Avoirs/{year}/',
    )
    stamp_out_invoice_enabled = fields.Boolean(
        string='Factures client',
        config_parameter='vendor_bill_stamp.out_invoice_enabled',
        default=False,
    )
    stamp_nc_path_out_invoice = fields.Char(
        string='Chemin factures client',
        config_parameter='vendor_bill_stamp.nc_path_out_invoice',
        default='/Factures/Clients/{year}/',
    )
    stamp_out_refund_enabled = fields.Boolean(
        string='Notes de crédit client',
        config_parameter='vendor_bill_stamp.out_refund_enabled',
        default=False,
    )
    stamp_nc_path_out_refund = fields.Char(
        string='Chemin notes de crédit client',
        config_parameter='vendor_bill_stamp.nc_path_out_refund',
        default='/Factures/Clients/Avoirs/{year}/',
    )
    stamp_out_quote_enabled = fields.Boolean(
        string='Devis / commandes client',
        config_parameter='vendor_bill_stamp.out_quote_enabled',
        default=False,
    )
    stamp_nc_path_out_quote = fields.Char(
        string='Chemin devis/commandes client',
        config_parameter='vendor_bill_stamp.nc_path_out_quote',
        default='/Devis/{year}/',
    )
