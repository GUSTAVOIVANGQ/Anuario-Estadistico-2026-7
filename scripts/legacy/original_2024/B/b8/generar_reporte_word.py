#!/usr/bin/env python3
"""
Script para generar un reporte en Word con:
- Portada
- Hoja de objetivo
- Contenido del README_complemento.md
- Figuras originales del anuario
- Conclusiones
"""

import os
import sys
from pathlib import Path

# Instalar python-docx si no está disponible
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("Instalando python-docx...")
    os.system(f"{sys.executable} -m pip install python-docx -q")
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement


def add_page_break(doc):
    """Añade un salto de página"""
    doc.add_page_break()


def set_cell_border(cell, **kwargs):
    """Establece bordes en celdas de tabla"""
    tcPr = cell._tcPr
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ("top", "left", "bottom", "right"):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            edge_el = OxmlElement(f'w:{edge}')
            edge_el.set(qn('w:val'), 'single')
            edge_el.set(qn('w:sz'), '12')
            edge_el.set(qn('w:space'), '0')
            edge_el.set(qn('w:color'), 'cccccc')
            tcBorders.append(edge_el)
    tcPr.append(tcBorders)


def crear_portada(doc):
    """Crea la portada del documento"""
    # Añade espacios
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()
    
    # Título principal
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("REPRODUCCIÓN DE FIGURAS")
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(43, 16, 85)  # Púrpura IFT
    
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle.add_run("Anuario Estadístico 2024 del IFT")
    subtitle_run.font.size = Pt(18)
    subtitle_run.font.color.rgb = RGBColor(123, 45, 142)
    
    # Espacios
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()
    
    # Subtítulo descriptivo
    desc = doc.add_paragraph()
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    desc_run = desc.add_run("Guía Técnica de Trazabilidad")
    desc_run.font.size = Pt(14)
    desc_run.italic = True
    
    desc2 = doc.add_paragraph()
    desc2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    desc2_run = desc2.add_run("Figuras A.1 a A.10")
    desc2_run.font.size = Pt(14)
    desc2_run.italic = True
    
    # Espacios
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()
    
    # Footer con fecha
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("Marzo 2026")
    footer_run.font.size = Pt(11)
    footer_run.font.color.rgb = RGBColor(107, 107, 107)
    
    add_page_break(doc)


def crear_hoja_objetivo(doc):
    """Crea la hoja de objetivo"""
    heading = doc.add_heading("Objetivo del Documento", level=1)
    heading_format = heading.paragraph_format
    heading_format.space_before = Pt(18)
    heading_format.space_after = Pt(12)
    
    # Asunto
    doc.add_heading("Asunto", level=2)
    asunto = doc.add_paragraph(
        "Documentar, por figura A.1 a A.10, las fuentes, fórmulas y el procesamiento "
        "que realizan los scripts del proyecto de reproducción de figuras."
    )
    asunto.paragraph_format.space_after = Pt(12)
    asunto.paragraph_format.line_spacing = 1.15
    
    # Objetivo
    doc.add_heading("Objetivo", level=2)
    objetivo = doc.add_paragraph(
        "Contar con una guía de trazabilidad técnica para validar cómo se reproducen "
        "las gráficas del Anuario Estadístico 2024 del IFT, desde los datos de entrada "
        "hasta los indicadores finales y el archivo de salida."
    )
    objetivo.paragraph_format.space_after = Pt(12)
    objetivo.paragraph_format.line_spacing = 1.15
    
    # Alcance
    doc.add_heading("Alcance", level=2)
    alcance_intro = doc.add_paragraph(
        "Este documento cubre exclusivamente los siguientes scripts:"
    )
    alcance_intro.paragraph_format.space_after = Pt(6)
    
    scripts = [
        "scripts/a1/figura_a1.py",
        "scripts/a2/figura_a2.py",
        "scripts/a3/figura_a3.py",
        "scripts/a4/figura_a4.py",
        "scripts/a5/figura_a5.py",
        "scripts/a6/figura_a6.py",
        "scripts/a7/figura_a7.py",
        "scripts/a8/figura_a8.py",
        "scripts/a9/figura_a9.py",
        "scripts/a10/figura_a10.py",
    ]
    
    for script in scripts:
        p = doc.add_paragraph(script, style='List Bullet')
        p.paragraph_format.space_after = Pt(2)
    
    add_page_break(doc)


def procesar_markdown(texto):
    """Convierte markdown simple a estructuras Word"""
    lines = texto.split('\n')
    return lines


def crear_contenido_principal(doc, readme_path):
    """Crea el contenido principal del documento desde el README"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procesar línea por línea
    lines = content.split('\n')
    
    skip_asunto_objetivo = False
    current_section = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Saltar las primeras secciones (ya están en hoja de objetivo)
        if line_stripped.startswith('## Asunto') or line_stripped.startswith('## Objetivo') or line_stripped.startswith('## Alcance'):
            skip_asunto_objetivo = True
            continue
        
        if skip_asunto_objetivo and (line_stripped.startswith('---') or line_stripped.startswith('## Figura')):
            skip_asunto_objetivo = False
        
        if skip_asunto_objetivo:
            continue
        
        # Procesar encabezados (markdown)
        if line.startswith('## '):
            heading_text = line.replace('## ', '').strip()
            h = doc.add_heading(heading_text, level=1)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(6)
        
        elif line.startswith('### '):
            heading_text = line.replace('### ', '').strip()
            h = doc.add_heading(heading_text, level=2)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(4)
        
        elif line.startswith('#### '):
            heading_text = line.replace('#### ', '').strip()
            h = doc.add_heading(heading_text, level=3)
            h.paragraph_format.space_before = Pt(6)
            h.paragraph_format.space_after = Pt(3)
        
        # Procesar negritas/código
        elif line_stripped.startswith('**') and line_stripped.endswith('**'):
            text = line_stripped.replace('**', '')
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            p.paragraph_format.space_after = Pt(3)
        
        elif line_stripped.startswith('```'):
            # Bloque de código
            code_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('```'):
                code_lines.append(lines[j])
                j += 1
            if code_lines:
                code_text = '\n'.join(code_lines)
                p = doc.add_paragraph(code_text, style='List Number')
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(6)
                pPr = p._element.get_or_add_pPr()
                pStyle = pPr.find(qn('w:pStyle'))
                if pStyle is not None:
                    pStyle.set(qn('w:val'), 'Normal')
        
        elif line.startswith('- '):
            bullet_text = line.replace('- ', '').strip()
            p = doc.add_paragraph(bullet_text, style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
        
        elif line.startswith('1. '):
            numbered = line.split('. ', 1)[1] if '. ' in line else line
            p = doc.add_paragraph(numbered, style='List Number')
            p.paragraph_format.space_after = Pt(2)
        
        elif line_stripped == '---':
            # Línea horizontal - saltar
            continue
        
        elif line_stripped and not line_stripped.startswith('!'):
            # Párrafo normal (ignorar imágenes markdown)
            if not line_stripped.startswith('!['):
                p = doc.add_paragraph(line)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.line_spacing = 1.15


def insertar_figuras_originales(doc, original_pictures_path):
    """Inserta las figuras originales del anuario"""
    doc.add_page_break()
    heading = doc.add_heading("Figuras Originales del Anuario IFT 2024", level=1)
    heading.paragraph_format.space_before = Pt(18)
    heading.paragraph_format.space_after = Pt(12)
    
    intro = doc.add_paragraph(
        "A continuación se presentan las figuras originales del Anuario Estadístico 2024 "
        "del IFT, que sirvieron como referencia para la reproducción mediante scripts Python."
    )
    intro.paragraph_format.space_after = Pt(12)
    intro.paragraph_format.line_spacing = 1.15
    
    # Buscar las imágenes originales
    picture_files = sorted(Path(original_pictures_path).glob('*.png'))
    
    for pic_file in picture_files:
        try:
            # Nombre de la figura
            figure_name = pic_file.stem  # A1, A2, etc.
            
            # Añade encabezado de figura
            fig_heading = doc.add_heading(f"Figura {figure_name.upper()}", level=2)
            fig_heading.paragraph_format.space_before = Pt(12)
            fig_heading.paragraph_format.space_after = Pt(6)
            
            # Añade la imagen
            try:
                doc.add_picture(str(pic_file), width=Inches(5.5))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                last_paragraph.paragraph_format.space_after = Pt(12)
            except Exception as e:
                print(f"Error al insertar imagen {pic_file}: {e}")
                p = doc.add_paragraph(f"[Imagen no disponible: {pic_file.name}]")
                p.paragraph_format.space_after = Pt(6)
            
            # Pequeña nota de fuente
            note = doc.add_paragraph(f"Fuente: {figure_name.upper()}.png - Anuario Estadístico 2024 del IFT")
            note.paragraph_format.space_after = Pt(12)
            note_format = note.runs[0]
            note_format.font.size = Pt(9)
            note_format.italic = True
            note_format.font.color.rgb = RGBColor(128, 128, 128)
        
        except Exception as e:
            print(f"Error procesando {pic_file}: {e}")
            continue


def crear_conclusiones(doc):
    """Crea la sección de conclusiones"""
    doc.add_page_break()
    heading = doc.add_heading("Conclusiones", level=1)
    heading.paragraph_format.space_before = Pt(18)
    heading.paragraph_format.space_after = Pt(12)
    
    conclusions = [
        "Se ha reproducido exitosamente el 100% de las figuras A.1 a A.10 del Anuario "
        "Estadístico 2024 del IFT utilizando Python y librerías de visualización (matplotlib).",
        
        "Cada figura cuenta con una documentación técnica detallada que incluye: fuentes "
        "de datos (INEGI, IFT, Secretaría de Economía), fórmulas aplicadas, identificación "
        "de filas/columnas específicas, y transformaciones realizadas.",
        
        "Las figuras A.1 a A.6 trabajan con datos agregados de instituciones públicas "
        "(PIB trimestral, inversión, ingresos de operadores), mientras que A.7 a A.10 "
        "utilizan microdatos de la Encuesta Nacional de Ingresos y Gastos de los Hogares "
        "(ENIGH 2022) con ponderación por factor de expansión.",
        
        "Se han identificado discrepancias menores entre los datos originales y los "
        "presentados en el PDF del anuario, atribuibles a redondeamientos, cambios "
        "en las cifras reportadas por operadores, y variaciones de metodología de cálculo.",
        
        "Este documento técnico proporciona trazabilidad completa y permite validar, "
        "reproducir y extender el análisis con nuevos períodos o modificaciones metodológicas.",
    ]
    
    for conclusion in conclusions:
        p = doc.add_paragraph(conclusion, style='List Bullet')
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.15
    
    # Nota final
    doc.add_paragraph()
    final_note = doc.add_paragraph(
        f"Documento generado: marzo 2026"
    )
    final_note.paragraph_format.space_before = Pt(18)
    final_note_format = final_note.runs[0]
    final_note_format.font.size = Pt(10)
    final_note_format.italic = True
    final_note_format.font.color.rgb = RGBColor(107, 107, 107)


def main():
    # Rutas
    base_path = Path(__file__).parent.parent
    readme_path = base_path / "README_complemento.md"
    original_pictures_path = base_path / "original_pictures"
    output_path = base_path / "Reporte_Tecnico_A1_A10.docx"
    
    # Validar archivos
    if not readme_path.exists():
        print(f"Error: No se encuentra {readme_path}")
        return False
    
    if not original_pictures_path.exists():
        print(f"Advertencia: No se encuentra {original_pictures_path}")
    
    # Crear documento
    print("Creando documento Word...")
    doc = Document()
    
    # Configurar márgenes
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # Construir documento
    print("  - Creando portada...")
    crear_portada(doc)
    
    print("  - Creando hoja de objetivo...")
    crear_hoja_objetivo(doc)
    
    print("  - Insertando contenido principal...")
    crear_contenido_principal(doc, readme_path)
    
    print("  - Insertando figuras originales...")
    if original_pictures_path.exists():
        insertar_figuras_originales(doc, original_pictures_path)
    
    print("  - Creando conclusiones...")
    crear_conclusiones(doc)
    
    # Guardar documento
    print(f"Guardando documento en {output_path}...")
    doc.save(str(output_path))
    
    print(f"✓ Documento generado exitosamente: {output_path}")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
