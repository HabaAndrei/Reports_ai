## =>>>>  test3


import pdfplumber
from nltk.tokenize import sent_tokenize
import re
from langchain.text_splitter import CharacterTextSplitter
from openai import OpenAI
from InstructorEmbedding import INSTRUCTOR
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
#from deepmultilingualpunctuation import PunctuationModel

import psycopg2

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_key = os.getenv('DATABASE_key')
USER_key = os.getenv('USER_key')
PASSWORD_key = os.getenv('PASSWORD_key')
HOST_key = os.getenv('HOST_key')
PORT_key = os.getenv('PORT_key')
OPEN_API_KEY = os.getenv('OPEN_API_KEY')

client = OpenAI(api_key=OPEN_API_KEY)



#model_punctuatie = PunctuationModel()

import requests
import os


def impartimProp(array, numarDeProp):
    try:
        arFinal = []
        while len(array):
            ok = array[0: numarDeProp]
            arFinal.append(ok)
            if len(ok) == len(array):
                array = []
            else:
                array = array[len(ok): len(array)]
        return arFinal
    except:
        return []


def download_pdf(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifică dacă cererea a avut succes

        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)

        #print(f"PDF downloaded and saved successfully at {file_path}")

    except requests.exceptions.RequestException as e:
        #print(f"Error downloading the PDF: {e}")
        return e


def delete_pdf(filename):
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            #print(f"PDF deleted successfully from {file_path}")
    except OSError as e:
        #print(f"Error deleting the PDF: {e}")
        return e




def formar_text_ai(text):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": '''
                         \nTask: Tu esti un bot de inteligenta artificiala care primesti un text, pe care il formatezi corect in limba romana. 
                         \nAttention: Trebuie sa pui toate semnele de punctuatie pentru face propozitii. 
                         \nBehavior: Dupa terminarea unei propozitii sa ii adaugi un '\n' exemplu: 'Dan este cuminte '\n'' .
                         \nCharge: Elimina caracterele repetitive care nu au sens.
                         \nTechnique: Daca tascul este complex, imparte lucrurile de facut si fa-le pe rand
                         '''
             },
            {"role": "user",
             "content": text}
        ],
    )

    return completion.choices[0].message.content



def reformativText_overlap(text):
    try:
        result = model_punctuatie.restore_punctuation(text)
        text_splitter = CharacterTextSplitter(
            separator="",
            chunk_size=800,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        text_cu_split = text_splitter.create_documents([result])
        arCuProp = [doc.page_content for doc in text_cu_split]

        return arCuProp
    except:
        return []

##################################################
#################################################


chroma_client = chromadb.HttpClient(host="localhost", port=8000)


class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:

        sentences = input

        model = INSTRUCTOR('hkunlp/instructor-base')
        arEmb = []
        for prop in sentences:
            embeddings = model.encode([['It represents a financial report but also the presentation of the company', prop]])
            arEmb.extend(embeddings)
        # Convert embeddings to a list of lists
        embeddings_as_list = [embedding.tolist() for embedding in arEmb]

        return embeddings_as_list


collection = chroma_client.get_or_create_collection(name="reports", embedding_function=MyEmbeddingFunction())

# chroma_client.delete_collection(name="reports")


# col = collection.get()
#
# dataNou = zip(col['ids'], col['documents'])
#
# print(tuple(dataNou))

# print(collection.get()['ids'])
# arrayCuDateAdaugate = collection.get()['documents']
# for text in arrayCuDateAdaugate:
#     print('\n\n', text, '\n\n')

# print(collection.get()['documents'][0], type(collection.get()['documents']))



# print(chroma_client.list_collections())

def adaugamInChroma(nume, token, paragraf, nr_pag ):
    lungime = len(collection.get()['ids'])
    if lungime < 1:
        try:
            collection.add(
                documents=[paragraf],
                metadatas=[{"nume": nume, "token": token, "nr_pag": nr_pag}],
                ids=['1']
            )
            #print('am adaugat cu succes cu id', str(lungime + 1))
        except ZeroDivisionError:
            #print('eroare id 1')
            return ''
    else:
        try:
            collection.add(
                documents=[paragraf],
                metadatas=[{"nume":nume, "token": token, "nr_pag": nr_pag }],
                ids=[str(lungime + 1)]
            )
            #print('am adaugat cu succes cu id', str(lungime + 1))
        except ZeroDivisionError:
            #print('eroare id mai mare ca 1')
            return ''





def res_from_query(nume_sau_token, intrebare):
    results_nume = collection.query(
        query_texts=[intrebare],
        n_results=4,
        where={"nume": nume_sau_token}
    )

    results_token = collection.query(
        query_texts=[intrebare],
        n_results=4,
        where={"token": nume_sau_token}
    )

    arMareCuRez = []

    for string in results_nume['documents'][0]:
        if len(string):
            arMareCuRez.append(string)

    for string in results_token['documents'][0]:
        if len(string):
            arMareCuRez.append(string)
    return arMareCuRez

##########################################################


conn = psycopg2.connect(database=DATABASE_key, user=USER_key,
                                password=PASSWORD_key, host=HOST_key, port=PORT_key)
pg_client = conn.cursor()


def verificamInserarea(numeCompanie):
    try:

        pg_client.execute("select nume_companie from manage_insert where nume_companie = %s ", (numeCompanie,))
        data = pg_client.fetchall()

        if data and data[0] and data[0][0]:
            return True
        else:
            return False
    except Exception as e:
        #print('avem eroare la verificarea din baza de date PG', e)
        return False

def insertInPg(numeCompanie):
    try:
        pg_client.execute("insert into manage_insert (nume_companie, nume_raport) values (%s, %s) ", (numeCompanie, 'Raport 2023'))
        conn.commit()
        #print('s a inserat cu succes!!')

    except Exception as e:
        #print('avem o eroare la inserare de date!!!!!!!!!!!!!', e)
        return ''

def insertInPgPage(numeCompanie, nr_pag):
    try:
        pg_client.execute("insert into manage_insert_pag (nume_companie, nr_pag) values (%s, %s) ",
                          (numeCompanie, nr_pag))
        conn.commit()
        #print('s a inserat cu succes numarul paginii!!')

    except Exception as e:
        #print('avem o eroare la inserare de date nr pag!!!!!!!!!!!!!', e)
        return ''


def verifyPagInPg(numeCompanie, nr_pag):
    try:
        pg_client.execute("select nume_companie from manage_insert_pag where nume_companie = %s  and nr_pag = %s ", (numeCompanie, nr_pag))
        data = pg_client.fetchall()

        if data and data[0] and data[0][0]:
            return True
        else:
            return False
    except Exception as e:
        #print('avem eroare la verificarea din baza de date PG', e)
        return False
