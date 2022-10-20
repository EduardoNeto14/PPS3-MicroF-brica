import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

class DataframeMetadata:
    def __init__(self, name : str, df : pd.DataFrame):
        self.name = name
        self.df = df

class XMLSpreasheet:  
    def __init__(self, path_to_spreadsheet: str):
        self.path = path_to_spreadsheet
        self.no_of_worksheets = 0
        self.worksheets = []

    def get_worksheet(self, name : str):
        for worksheet in self.worksheets:
            if worksheet.name == name:
                return worksheet.df

    def _parse_xml_worksheet(self, xml_soup : BeautifulSoup):
        df = None

        for i, row in enumerate(xml_soup.findAll("Row")):
            row_to_append = []

            for cell in row.findAll("Cell"):
                row_to_append.append(cell.Data.text)
            
            if i == 0:
                df = pd.DataFrame(columns = row_to_append)
            else:
                df.loc[len(df)] = row_to_append

            row_to_append = []

        if df is not None:
            return df
        else:
            return None

    def parse_spreadsheet(self):
        with open(self.path, "r") as f:
            data = f.read()
        
        soup = BeautifulSoup(data, "xml")
        for sheet in soup.findAll("Worksheet"):
            result = self._parse_xml_worksheet(sheet)

            if result is not None:
                self.worksheets.append(DataframeMetadata(sheet.get("ss:Name"), result))
                self.no_of_worksheets += 1

        return True

parser_report = XMLSpreasheet("MachineReport_CITEVE.xml")
parser_report.parse_spreadsheet()
print(parser_report.get_worksheet("Machines"))

parser_export = XMLSpreasheet("Export_CITEVE/ExportExcel_2022-10-06_220240.xml")
parser_export.parse_spreadsheet()

rep = parser_export.get_worksheet("Report").replace(r'^\s+$', np.nan, regex=True)
print(parser_export.get_worksheet("Stock Material").replace(r'^\s+$', np.nan, regex=True))
print(parser_export.get_worksheet("Parts").replace(r'^\s+$', np.nan, regex=True))
cut = parser_export.get_worksheet("Cutting Log").replace(r'^\s+$', np.nan, regex=True)

common = list(set(rep).intersection(cut))
common.remove("Cutting Log")

rep_cut = pd.merge(rep, cut, how = "outer", on = "Cutting Log")

for c in common:
    comp = np.where(rep_cut[c+"_x"] == rep_cut[c+"_y"], True, False)
    
    if False in comp:
        print(f"{c}: Diferente")
    else:
        print(f"{c}: Igual")
        rep_cut.drop(c+"_y", inplace=True, axis=1)
        rep_cut.rename(columns={c+"_x" : c}, inplace=True)

to_keep = [
    "Created On",
    "Machine User",
    "Parts Area (m²)",
    "Number Of Parts",
    "Cut Order",
    "Oper_StartDate",
    "ProductionWorkOrders",
    "Processed",
    "Cutting Log",
    "State",
    "Material",
    "Cutting Log Representation",
    "Cut Start",
    "Cut End",
    "Cut Time (s)",
    "Tool",
    "Insert",
    "Count"
]

rep_cut = rep_cut[to_keep]
rep_cut.to_csv("final.csv", index=False)        