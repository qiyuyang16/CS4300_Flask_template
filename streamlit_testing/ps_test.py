from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
import pathlib

path = "./Nurse.pdf"
parser = HierarchyParser()
file_path = pathlib.Path("test-pdf.json")

source = FileSource(path)

document = parser.parse_pdf(source)

from pdfstructure.printer import JsonFilePrinter
printer = JsonFilePrinter()
file_path = pathlib.Path("test-pdf.json")

printer.print(document, file_path=str(file_path.absolute()))