from odoo import http, fields, api
from odoo.http import request
from odoo.tools.misc import xlwt
import io
import base64
import werkzeug
from datetime import date, datetime, timedelta
import ast

import logging

_logger = logging.getLogger(__name__)


class ExportList(http.Controller):

    @http.route('/export_fichier/<data_back>', auth='user', website=True, csrf=False, type='http', method=['POST'])
    def indexExport(self, data_back, **post):
        data_back = data_back.split(",")

        # retourne des choses au template export est un id
        fields_model = http.request.env['ir.model.fields'].search([('model', '=', data_back[0]),
                                                                   ('store', '=', True),
                                                                   ('name', 'not in', ['create_date', 'write_date'])])

        return http.request.render('export_view_parthenay.export', {
            'fields_model': fields_model,
            'data_back': data_back,
        })

    @http.route('/tableau_export_fichier/<fields_checked>/<data_back>', auth='user', website=True, type='http',
                csrf=False, method=['POST'])
    def tableauExport(self, fields_checked, data_back, **post):
        ids = []
        vals = {}

        data_back = ast.literal_eval(data_back)  # On reconstitue le tableau qui était en format str
        for data in data_back[1:]:
            ids.append(int(data))

        fields_checked = fields_checked.split(",")
        object_field = http.request.env['ir.model.fields']
        # Recherche les ids dans la table (ecole.partner.school)
        value_model = http.request.env[data_back[0]].browse(ids)
        for field_checked in fields_checked:
            field_model = object_field.search([('model', '=', data_back[0]),
                                               ('field_description', '=', field_checked)], limit=1)
            if field_model.ttype == "date":
                libelle = field_model.field_description  # Libellé français
                search_field = field_model.name  # Nom de la colonne
                value_date = []  # Récupère les dates converties
                for val in value_model:
                    if val.mapped(search_field):
                        if val.mapped(search_field)[0]:
                            value_date.append(datetime.strptime(val.mapped(search_field)[0], "%Y-%m-%d").strftime("%d/%m/%Y"))
                        else:
                            value_date.append("-")
                    else:
                        value_date.append("-")
                vals.update({
                    libelle: value_date,
                })
            elif field_model.ttype == "many2one":
                result = []
                libelle = field_model.field_description
                if field_model.field_description != "Période":
                    search_field = field_model.name + '.name'
                else:
                    search_field = field_model.name + '.school_years'
                for val in value_model:
                    if val.mapped(search_field):
                        result.append(val.mapped(search_field)[0])
                    else:
                        result.append("-")
                vals.update({
                    libelle: result,
                })
            else:
                result = []
                libelle = field_model.field_description
                search_field = field_model.name
                for val in value_model:
                    if val.mapped(search_field):
                        if val.mapped(search_field)[0] == True:
                            result.append('OUI')
                        elif val.mapped(search_field)[0] == False or val.mapped(search_field)[0] == '':
                            result.append('NON')
                        else:
                            result.append(val.mapped(search_field)[0])
                    else:
                        result.append('-')

                # result_values = value_model.mapped(search_field)
                vals.update({
                    libelle: result,
                })

        return http.request.render('export_view_parthenay.modal', {
            'fields_checked': fields_checked,
            'vals': vals,
            'ids': ids,
        })

    @http.route('/telechargement_fichier/', auth='user', website=True, type='http', method=['POST'])
    def download_file(self, **post):
        if request.httprequest.method == 'POST':
            if post.get('input_download_file', False):
                if post.get('vals', False):
                    # On reconstitue le dictionnaire qui était en format str
                    data_result = ast.literal_eval(post.get('vals', False))
                    # Nom du fichier de sortie
                    name_file = post.get('name_file', False)
                    filename = str(name_file) + '.xls'

                    # Style du tableau Excel
                    workbook = xlwt.Workbook()
                    worksheet = workbook.add_sheet('Export')
                    font = xlwt.Font()
                    font.bold = True
                    for_left = xlwt.easyxf(
                        "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
                    for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left")
                    for_center_bold = xlwt.easyxf("font: bold 1, color black; align: horiz center")
                    style = xlwt.easyxf(
                        'font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')

                    alignment = xlwt.Alignment()  # Create Alignment
                    alignment.horz = xlwt.Alignment.HORZ_RIGHT
                    style = xlwt.easyxf('align: wrap yes')
                    style.num_format_str = '0.00'

                    worksheet.row(0).height = 500
                    worksheet.col(0).width = 4000
                    worksheet.col(1).width = 4000
                    borders = xlwt.Borders()
                    borders.bottom = xlwt.Borders.MEDIUM
                    border_style = xlwt.XFStyle()  # Create Style
                    border_style.borders = borders

                    # Traitement des données pour export
                    row = 0
                    column = 0
                    if row == 0:
                        for key, values in data_result.items():
                            worksheet.write(row, column, key, for_left)
                            i = 1
                            for value in values:
                                worksheet.write(row + i, column, value, for_left_not_bold)
                                i += 1
                            column += 1

                    fp = io.BytesIO()
                    # Sauvegarde des fichiers apres écriture (write)
                    workbook.save(fp)
                    # Stockage sous forme binaire du fichier dans la base Odoo (table export.student)
                    export_id = http.request.env['export.student'].create(
                        {'excel_file': base64.encodestring(fp.getvalue()),
                         'file_name': filename})
                    fp.close()

                    url_file = '/web/binary/download_document_partner?model=export.student&field=excel_file&id=' + str(
                        export_id.id) + '&filename=' + filename

                    return werkzeug.utils.redirect(url_file)
