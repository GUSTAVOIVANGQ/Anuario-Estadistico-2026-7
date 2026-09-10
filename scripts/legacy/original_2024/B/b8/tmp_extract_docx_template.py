import glob
import re
import zipfile
import xml.etree.ElementTree as ET


def main() -> None:
    matches = glob.glob("*COCODI.docx")
    if not matches:
        print("No se encontro plantilla DOCX")
        return

    path = matches[0]
    with zipfile.ZipFile(path) as zf:
        xml_data = zf.read("word/document.xml")

    root = ET.fromstring(xml_data)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    paras = []
    for par in root.iter(f"{ns}p"):
        text = "".join((t.text or "") for t in par.iter(f"{ns}t")).strip()
        if text:
            paras.append(re.sub(r"\s+", " ", text))

    print("\n".join(paras[:250]))


if __name__ == "__main__":
    main()
