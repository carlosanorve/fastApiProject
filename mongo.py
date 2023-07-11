from pathlib import Path
from typing import Dict

import openpyxl
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from config import config


class MongoConnection:
    def __init__(self, database):
        self.host = config.DB_HOST
        self.port = config.DB_PORT
        self.user = config.USER
        self.password = config.PASSWORD
        self.options = config.OPTIONS
        self.uri = config.URI

        self.database = database

        self.client = None
        self.db = None

    def connect(self):
        print("connectando...")
        if self.uri:
            string_connection = self.uri
            self.client = MongoClient(string_connection, server_api=ServerApi('1'))
        else:
            string_connection = f'mongodb://{self.user}:{self.password}@{self.host}:{self.port}{self.options}'
            self.client = MongoClient(string_connection, retryWrites=False)

        self.db = self.client[self.database]
        print("connectado")

    def disconnect(self):
        if self.client:
            print("Desconenctando...")
            self.client.close()
            print("Desconenctado")


class Collections(MongoConnection):
    def get_collection_names(self):
        if self.db is not None:
            return self.db.list_collection_names()
        else:
            raise Exception("No se ha establecido una conexión a la base de datos.")


class Internationalization(Collections):
    def __init__(self):
        super().__init__("internationalization")

    def get_screens(self, *, sync=False):
        screens = {}
        collections = self.get_collection_names()
        available_sync = False

        for collection in collections:
            _collection = self.db[collection]
            documents = _collection.find()
            for document in documents:
                screens.setdefault(document['SCREEN'], {})
                data = screens.get(document['SCREEN'], {})
                data.setdefault("NAME", document['SCREEN'])
                data.setdefault("COUNTRIES", [])
                data['COUNTRIES'].append({"NAME": collection})
        for screen in screens:
            differences = list(set(collections).difference(set([n["NAME"] for n in screens[screen]['COUNTRIES']])))
            if differences:
                available_sync = True
                screens[screen][
                    'WARNING'] = differences if sync else f"THIS SCREEN DO NOT EXIST IN SCHEMA {differences if len(differences) > 1 else differences[0]}"
                for difference in differences:
                    screens[screen]['COUNTRIES'].append({"NAME": difference, "WARNINGS": {"MESSAGE":
                                                                                              f"THIS SCREEN DO NOT EXIST HERE"}})
        screens = list(screens.values())

        return {"SYNC": available_sync, "DATA": screens}

    def get_screens_details(self, screen):
        collections = self.get_collection_names()

        _data = {}
        for collection in collections:
            _country_data = self.db[collection]
            documents = _country_data.find_one({"SCREEN": screen})
            values = (documents or {}).get("VALUES")
            if values:
                for key, value in values.items():
                    _data.setdefault(key, {"KEY": key, "VALUE": []})
                    _data[key]["VALUE"].append({
                        "country": collection,
                        "value": value.replace("\\n", "\n")
                    })
        for data in _data:
            for e in collections:
                if e not in [d["country"] for d in _data[data]["VALUE"]]:
                    _data[data]["VALUE"].append({"country": e, "value": "", "warning": "tag not exist in this country"})

        return {"countries": collections, "data": list(_data.values())}

    def add_new_tag(self, *, screen: str, tag: str, values: Dict[str, str]):
        """

        :param screen:
        :param tag:
        :param values: {"global": "value", "country": "value"}
        :return:
        """
        collections = self.get_collection_names()
        for collection in collections:
            self._add_tag(country=collection, screen=screen, tag=tag, value=values.get(collection, ""))

    def add_new_screen(self, *, screen_name: str, connection=None):
        countries = self.get_collection_names()
        for country in countries:
            coll = self.db[country] if (connection is None) else connection
            coll.insert_one({"SCREEN": screen_name, "VALUES": []})

    def _add_tag(self, *, country, screen, tag, value):
        coll = self.db[country]
        document_exists = coll.find_one({'SCREEN': screen})
        if not document_exists:
            self.add_new_screen(screen_name=screen, connection=coll)

        coll.update_one(
            {'SCREEN': screen},
            {'$set': {f'VALUES.{tag}': value}}
        )

    def sync_schemas(self):
        screens = self.get_screens(sync=True)
        for screen in screens:
            for country in screen.get("WARNING", []):
                coll = self.db[country]
                coll.insert_one({"SCREEN": screen["NAME"], "VALUES": []})

    def _parse_file(self):
        # Leer el archivo excel
        excel_file = Path(r"C:\Users\carlo\Downloads\InternacionalizaciónAdmin.xlsx")

        workbook = openpyxl.load_workbook(excel_file)
        sheet = workbook.active

        # Obtener los encabezados de las columnas
        headers = [cell.value for cell in sheet[1]]

        generated_data = {country: {} for country in self.get_collection_names()}

        # Recorrer las filas y convertirlas a diccionarios
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_data = dict(zip(headers, row))

            key = row_data.get("Key", "").split("_")
            if not key:
                continue

            screen = key.pop(0)
            key_tag = "_".join(key)

            for k in generated_data:
                generated_data[k].setdefault(screen, {
                    "SCREEN": screen,
                    "VALUES": {}
                })
                generated_data[k][screen]["VALUES"].update({key_tag: row_data.get(k.upper(), "") or ""})
        return generated_data

    def restart_and_import_file(self):
        data = self._parse_file()
        for country, values in data.items():
            self.restart_collection(country)
            collection = self.db[country]
            collection.insert_many(list(values.values()))

    def drop_collection(self, collection_name):
        collection = self.db[collection_name]
        collection.drop()

    def create_collection(self, collection_name):
        self.db.create_collection(collection_name)

    def empty_collection(self, collection_name):
        collection = self.db[collection_name]
        collection.delete_many({})

    def restart_collection(self, collection_name):
        self.drop_collection(collection_name)
        self.create_collection(collection_name)


class Components(Collections):
    def __init__(self):
        super().__init__("components")

    def import_data(self, data):
        ...
