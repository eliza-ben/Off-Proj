from twist_old.parser import parse_twist_multi
from twist_old.export import export_csv_and_excel

if __name__ == "__main__":
    xml_path = "data/Sample_Parser.xml"

    doc = parse_twist_multi(r"C:\\Users\\FRR56\\PyCharmMiscProject\\data\\Sample_Parser.xml")

    print("electronicStatements:", len(doc.electronic_statement_list))
    print("statements total:", sum(len(es.statement_list) for es in doc.electronic_statement_list))
    print("services total:", sum(len(st.services) for es in doc.electronic_statement_list for st in es.statement_list))

    #export_csv_and_excel(doc, "output")

    print("Done")
