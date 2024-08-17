## => test3
from variabile import arPdfPage
import pdfplumber
from manage_rap import (insertInPg, download_pdf, verificamInserarea, delete_pdf,
                        impartimProp, adaugamInChroma, reformativText_overlap, verifyPagInPg, insertInPgPage)





def extract_text_from_pdf(nume, token, pdf_path):

    # print(pdf_path)
    pdf_path_local =  token + '.pdf'

    if verificamInserarea(token) == True:
        #print('deja a fost inserat ', token)
        return

    download_pdf(pdf_path, pdf_path_local)

    try:
        with pdfplumber.open(pdf_path_local) as pdf:
            i = 0
            for page in pdf.pages:
                i += 1

                if verifyPagInPg(token, i) == True:
                    #print('sarim peste pagina =>>', i)
                    break
                text = page.extract_text()
                # print(text, '=<<<<<<<<<<<<<<<<<<<<<<<<<<<,, text extras de pe pagina \n')

                text_reformatatInAr = reformativText_overlap(text)
                arDeArCuProp = impartimProp(text_reformatatInAr, 2)

                for ar_fraza in arDeArCuProp:
                    fraza = ' '.join(ar_fraza)
                    # print(fraza, '\n', '----------------- fraza de adugat in chroma  \n' )

                    adaugamInChroma(nume, token, fraza, i)

                insertInPgPage(token, i)

        insertInPg(token)
        delete_pdf(pdf_path_local)
    except:
        return ''



def proccessData():
    for index in range(0, 88, 1):
        obiectCuDate = arPdfPage[index]
        href, token, nume = obiectCuDate.values()
        #print(href, token, nume)
        extract_text_from_pdf(nume, token, href)


#proccessData()


