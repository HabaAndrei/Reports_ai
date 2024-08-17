# ### => test3


from flask import Flask
import chromadb
from openai import OpenAI
from flask_cors import CORS
from flask import Flask, request, Response
from manage_rap import  res_from_query
import json
from thefuzz import process, fuzz
from dotenv import load_dotenv
import os

load_dotenv()



app = Flask(__name__)
CORS(app)

OPEN_API_KEY = os.getenv('OPEN_API_KEY')
client = OpenAI(api_key=OPEN_API_KEY)



arNumeTokeni = [
    "FONDUL PROPRIETATEA", "FP", "OIL TERMINAL S.A.", "OIL", "OMV PETROM S.A.", "SNP", "TTS (TRANSPORT TRADE SERVICES) S.A.", "TTS", "BANCA TRANSILVANIA S.A.", "TLV", "SSIF BRK FINANCIAL GROUP SA",
    "BRK", "SOCIETATEA ENERGETICA ELECTRICA S.A.", "EL", "BRD - GROUPE SOCIETE GENERALE S.A.", "BRD", "TERAPLAST SA", "TRP", "S.N.G.N. ROMGAZ S.A.", "SNG", "SOCIETATEA DE PRODUCERE A ENERGIEI ELECTRICE IN HIDROCENTRALE HIDROELECTRICA S.A.", "H2O",
    "PREBET SA AIUD", "PREB", "SPHERA FRANCHISE GROUP", "SFG", "IMPACT DEVELOPER & CONTRACTOR S.A.", "IMP", "ONE UNITED PROPERTIES", "ONE", "BURSA DE VALORI BUCURESTI SA", "BVB", "S.N.T.G.N. TRANSGAZ S.A.", "TGN",
    "ZENTIVA S.A.", "SCD", "S.N. NUCLEARELECTRICA S.A.", "SNN", "TRANSILVANIA BROKER DE ASIGURARE SA", "TBK", "Digi Communications N.V.", "DIGI", "ANTIBIOTICE S.A.", "ATB", "BIOFARM S.A.", "BIO",
    "AQUILA PART PROD COM", "AQ", "C.N.T.E.E. TRANSELECTRICA", "TEL", "CHIMCOMPLEX BORZESTI SA ONESTI", "CRC", "COMPA S. A.", "CMP", "ALUMIL ROM INDUSTRY S.A.", "ALU", "S.C AAGES S.A.", "AAG",
    "Med Life S.A.", "M", "EVERGENT INVESTMENTS S.A.", "EVER", "ROMCARBON SA", "ROCE", "CONPET SA", "COTE", "SOCEP S.A.", "SOCP", "IAR SA Brasov", "IARV",
    "AEROSTAR S.A.", "ARS", "FARMACEUTICA REMEDIA SA", "RMAH", "PURCARI WINERIES PUBLIC COMPANY LIMITED", "WINE", "ROMCAB SA", "MCAB", "ROMPETROL RAFINARE S.A.", "RRC", "ELECTROMAGNETICA SA", "ELMA",
    "TURBOMECANICA S.A.", "TBM", "ROMPETROL WELL SERVICES S.A.", "PTR", "ROPHARMA SA", "RPH", "CARBOCHIM S.A.", "CBC", "PATRIA BANK S.A.", "PBK", "INFINITY CAPITAL INVESTMENTS S.A.", "INFINITY",
    "ALRO S.A.", "ALR", "LONGSHIELD INVESTMENT GROUP S.A.", "SIF4", "LION CAPITAL S.A.", "LION", "UCM RESITA S.A.", "UCM", "ROCA INDUSTRY HOLDINGROCK1 S.A.", "ROC1", "TURISM, HOTELURI, RESTAURANTE MAREA NEAGRA S.A.", "EFO",
    "SINTEZA S.A.", "STZ", "UAMT S.A.", "UAM", "PREFAB SA", "PREH", "SIF HOTELURI SA", "CAOR", "ALTUR S.A.", "ALT", "BERMAS S.A.", "BRM", "COMPANIA ENERGOPETROL S.A.", "ENP",
    "SANTIERUL NAVAL ORSOVA S.A.", "SNO", "ARTEGO SA", "ARTE", "COMELF S.A.", "CMF", "TURISM FELIX S.A.", "TUFE", "MECANICA CEAHLAU", "MECF", "COMCM SA CONSTANTA", "CMCM",
    "PROMATERIS S.A.", "PPL", "ELECTROAPARATAJ S.A.", "ELJ", "MECANICA FINA SA", "MECE", "GRUPUL INDUSTRIAL ELECTROCONTACT S.A.", "ECT", "ARMATURA S.A.", "ARM", "CASA DE BUCOVINA-CLUB DE MUNTE", "BCM",
    "CEMACON SA", "CEON", "VES SA", "VESY", "UZTEL S.A.", "UZT"
]

def fuzzy_search(nume):
    arraySortat = process.extract(nume, arNumeTokeni, scorer=fuzz.ratio)
    top = arraySortat[0][0]
    return top



def writeInFile(text):
    with open('see_det.txt', 'w', encoding='utf-8') as f:
        f.write(text)


def generatingFunction(completion):
    for chunk in completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content.encode('utf-8')




functions = [
    {
        "name": "get_name",
        "description": "Selectam firma sau simbolul unei firme din discutie",
        "parameters": {
            "type": "object",
            "properties": {
                "nume": {
                    "type": "string",
                    "description": "Numele companiei sau simbolul acesteia"
                },
            },
            "required": ["nume"]
        }
    }
]

def retunMesFuzzy(arCuOb, intrebare):
    arMessage = [
            {"role": "system", "content": "Tu esti un bot de inteligenta artificiala care imi furnizeaza date dintr-un raport finannciar anual"},
            ]
    for ob in arCuOb:
        if ob['type'] == 'intrebare':
            arMessage.append({'role': 'user', 'content': ob['mes']})
        else:
            arMessage.append({'role': 'assistant', 'content': ob['mes']})
    arMessage.append({'role': 'user', 'content': intrebare})
    return arMessage

def returnMesFinal(arCuOb, intrebare, context_raspuns_chroma):
    arMessage = [
        {"role": "system",
         "content": "Tu esti un bot de inteligenta artificiala care imi furnizeaza date dintr-un raport finannciar anual"},
    ]

    for ob in arCuOb:
        if ob['type'] == 'intrebare':
            arMessage.append({'role': 'user', 'content': ob['mes']})
        else:
            arMessage.append({'role': 'assistant', 'content': ob['mes']})
    arMessage.append({"role": "user", "content": 'context : ' + context_raspuns_chroma + ' \n question: ' + intrebare})
    return arMessage


@app.route("/send_mes" , methods = ['POST'])
def send_mes():
    data = request.json
    ar_context = data['context']
    intrebare = data['intrebare']
    token = data['token']

    #completion = client.chat.completions.create(
    #   model="gpt-3.5-turbo",
    #    messages=retunMesFuzzy(ar_context, intrebare),
    #    functions=functions,
    #    function_call="auto"
    #)

    #message = completion.choices[0].message
    context_raspuns_chroma = ''

    arRes = res_from_query(token, intrebare)
    data = '. '.join(arRes)
    context_raspuns_chroma = data


    #if message.function_call:
    #    function_name = message.function_call.name
    #    arguments = json.loads(message.function_call.arguments)
    #    if function_name == 'get_name':
    #        nume_or_token = arguments['nume']
    #       nume_sau_token = fuzzy_search(nume_or_token)
    #        print('\n\n\n', nume_or_token, '=>>>>>>', nume_sau_token, '\n\n\n\n')
    #        arRes = res_from_query(nume_sau_token, intrebare)
    #        data = '. '.join(arRes)
    #        context_raspuns_chroma = data


    # print('context_raspuns_chroma =>>>>>>>> ',  context_raspuns_chroma , '\n\n\n\n')


    #print(returnMesFinal(ar_context, intrebare, context_raspuns_chroma))




    mesFinal = returnMesFinal(ar_context, intrebare, context_raspuns_chroma)

    arDeStr = []
    for ob in mesFinal:
        arDeStr.append(json.dumps(ob))
    writeInFile('\n'.join(arDeStr))

    res = client.chat.completions.create(
        model="gpt-4o",
        messages=mesFinal,
	stream=True,
    )

    return Response(generatingFunction(res), mimetype = "text/event-stream" )
    #final_res = res.choices[0].message.content
    #return final_res




if __name__ == '__main__':
    app.run(host='195.201.17.190', port=8007, debug=True)

