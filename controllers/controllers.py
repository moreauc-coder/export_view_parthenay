from odoo import http, fields, api
from odoo.http import request
from odoo.tools.misc import xlwt
import io
import base64

import logging
_logger = logging.getLogger(__name__)


class ExportList(http.Controller):

    @http.route('/export_fichier/', auth='user', website=True, type='http',csrf=True, method=['POST'])
    def indexExport(self, **post):

        # retourne des choses au template export est un id
        fields_model = http.request.env['ir.model.fields'].search([('model', '=', 'ecole.partner.school')])  # A rendre dynamique

        return http.request.render('export_view_parthenay.export', {
            'fields_model': fields_model,
        })

    @http.route('/tableau_export_fichier/<fields_checked>', auth='user', website=True, type='http', csrf=False, method=['POST'])
    def tableauExport(self, fields_checked, **post):

        return http.request.render('export_view_parthenay.modal', {
            'fields_checked': fields_checked.split(","),
        })

    @http.route('/Telechargement_Fichier/<checked_form_ecole_partner_school>', auth='user', website=True, type='http', method=['POST'])
    def download_file(self,**post):
        if request.httprequest.method == 'POST':
            if post.get('input_download_file', False):
                if post.get('checked_form_ecole_partner_school', False):
                    print("ok")

                    checked_form_ecole_partner_school = post.get('checked_form_ecole_partner_school', False)
                    print(checked_form_ecole_partner_school)
                    checked_form_ecole_partner_school = checked_form_ecole_partner_school.replace('[', '')
                    checked_form_ecole_partner_school = checked_form_ecole_partner_school.replace(']', '')
                    checked_form_ecole_partner_school = checked_form_ecole_partner_school.replace("'", '')
                    checked_form_ecole_partner_school = checked_form_ecole_partner_school.replace('"', '')
                    checked_form_ecole_partner_school = checked_form_ecole_partner_school.split(",")
                    print(checked_form_ecole_partner_school)

                    # Nom du fichier de sortie
                    name_file = post.get('name_file', False)
                    filename = str(name_file+'.xls')

                    # Style du tableau Excel
                    workbook = xlwt.Workbook()
                    worksheet = workbook.add_sheet('Export élèves')
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
                    counter = 0
                    # Nom et prénom de ou des enfants selectionnés obligatoire à la génération du fichier
                    if row == 0:
                        for rec in checked_form_ecole_partner_school:
                            worksheet.write(row, column, checked_form_ecole_partner_school[counter], for_left)
                            column = column + 1
                            counter = counter + 1
                            # for rec in checked_form_ecole_partner_school:
                            #     worksheet.write(row, column, rec, for_left)

                    fp = io.BytesIO()
                    # Sauvegarde des fichiers apres écriture (write)
                    workbook.save(fp)
                    # Stockage sous forme binaire du fichier dans la base Odoo (table export.student)
                    export_id = http.request.env['export.student'].create({'excel_file': base64.encodestring(fp.getvalue()),
                                                                                   'file_name': filename})
                    fp.close()

                            # Export the XLS file
                            # print("Writing file C:\\Samples\\Tutorial28 - export XLS file.xls.")
                            # workbook.easy_WriteXLSFile("C:\\Samples\\Tutorial28 - export XLS file.xls")

                            #     for libelle in libelles:
                            #         worksheet.write(row, column_libelle, libelle, for_left)
                            #         column_libelle += 1
                            # values_list = (student.partner_id.street, student.partner_id.city_id.name,
                            #                school_birthdate, student.school_place_of_birth.name)
                            # for value_list in values_list:
                            #     if not value_list:
                            #         value_list = ""
                            #     worksheet.write(row + 1, column, value_list, for_left_not_bold)
                            #     column += 1


                    urlfile = '/web/binary/download_document_partner?model=export.student&field=excel_file&id=' + str(
                        export_id.id) + '&filename=' + filename
                    import werkzeug
                    return werkzeug.utils.redirect(urlfile)








