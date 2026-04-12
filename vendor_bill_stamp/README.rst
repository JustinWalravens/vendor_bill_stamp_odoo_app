PDF Stamp & Nextcloud Sync
==========================

Automatically stamp vendor bills, customer invoices, credit notes and
quotations with their Odoo reference number, then push the PDF to a
configurable Nextcloud folder — organised by document type and year.

Features
--------

* Stamp the Odoo number on every page of the PDF at validation time
* Smart PDF detection: stamps the supplier's original PDF if present,
  otherwise falls back to the Odoo-generated version
* Nextcloud WebDAV sync with dynamic path variables:
  ``{year}``, ``{month}``, ``{day}``, ``{ref}``, ``{number}``
* Independent control per document type (vendor bills, credit notes,
  customer invoices, quotations)
* Live quotation sync: PDF updated on every save
* Missing Nextcloud folders are created automatically
* Full settings UI under **Settings → PDF Stamp**

Requirements
------------

* Odoo 17 Community or Enterprise
* Python: ``pypdf``, ``reportlab``
* Nextcloud with WebDAV (standard)
* ``sale`` module for quotation sync

Installation
------------

1. Copy the module to your addons path.
2. Install ``pypdf`` and ``reportlab`` in your Odoo Python environment::

    pip install pypdf reportlab

3. Update the app list and install **PDF Stamp & Nextcloud Sync**.
4. Configure under **Settings → PDF Stamp**.

Author
------

Walravens Justin — Belgian Odoo developer.
