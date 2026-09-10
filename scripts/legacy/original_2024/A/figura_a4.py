#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar la Figura A.4: Inversión privada en Telecomunicaciones por tipo de inversión
Replicando el estilo UI institucional de B.17 con chips exteriores y líneas cuadradas
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import os

# ─── Configuración del Logger y Rutas ─────────────────────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from _plot_data_logger import enable_plot_data_logging
    enable_plot_data_logging()
except ImportError:
    pass

def clean_numeric_column(col):
    """Limpia columnas numéricas que pueden tener comas y espacios"""
    if pd.isna(col):
        return 0.0
    if isinstance(col, (int, float)):
        return col
    col_str = str(col).strip()
    if col_str == '-' or col_str == '' or col_str == 'nan':
        return 0.0
    try:
        return float(col_str.replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        return 0.0

def main():
    base_path = Path(__file__).parent.parent
    repo_root = base_path.parent
    data_file = repo_root / "datos" / "A.4" / "TD_INVERSION_TELECOM_ITE_VA.csv"
    output_dir = repo_root / "output"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"Leyendo datos desde: {data_file}")
    
    try:
        df = pd.read_csv(data_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(data_file, encoding='latin1')
        except Exception as e:
            print(f"Error leyendo el archivo: {e}")
            return
            
    investment_cols = [' INV_INFRA_E ', ' INV_ACT_NO_TANG_E  ', ' INV_OTRO_ACT_E ', ' INV_NO_ESP_E ', ' INV_TOTAL_E ']
    
    for col in investment_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric_column)
            
    df_filtered = df[(df['ANIO'] >= 2013) & (df['ANIO'] <= 2023)].copy()
    yearly_totals = df_filtered.groupby('ANIO')[investment_cols].sum()
    yearly_totals_billions = yearly_totals / 1_000_000
    
    years = [int(y) for y in yearly_totals_billions.index.tolist()]
    infra = yearly_totals_billions[' INV_INFRA_E '].values
    otros = yearly_totals_billions[' INV_OTRO_ACT_E '].values 
    no_tangibles = yearly_totals_billions[' INV_ACT_NO_TANG_E  '].values
    no_especificada = yearly_totals_billions[' INV_NO_ESP_E '].values
    totals = yearly_totals_billions[' INV_TOTAL_E '].values
    
    # --- Configuración Estilo Institucional ---
    plt.rcParams['font.family'] = ['Noto Sans', 'DejaVu Sans', 'sans-serif']
    C_TEXT = '#3c3c3b'
    
    fig, ax = plt.subplots(figsize=(16, 8.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F8F8FA')
    
    # Categorías organizadas de forma secuencial
    CATEGORIAS = ['Infraestructura', 'Otros Activos', 'Activos No Tangibles', 'No Especificada']
    VALS_DICT = {
        'Infraestructura': infra,
        'Otros Activos': otros,
        'Activos No Tangibles': no_tangibles,
        'No Especificada': no_especificada
    }
    COLORES_DICT = {
        'Infraestructura': '#234244',
        'Otros Activos': '#4c7d7e',
        'Activos No Tangibles': '#64a0a1',
        'No Especificada': '#86adae'
    }
    
    x_pos = np.arange(len(years))
    width = 0.45  # Ancho esbelto idéntico al esquema de B.17
    
    # --- Construcción de Barras Apiladas ---
    bottoms = np.zeros(len(years))
    bottoms_dict = {}
    
    for cat in CATEGORIAS:
        vals = VALS_DICT[cat]
        bottoms_dict[cat] = bottoms.copy()
        ax.bar(x_pos, vals, width, bottom=bottoms, color=COLORES_DICT[cat], label=cat, edgecolor='white', linewidth=0.5, zorder=3)
        bottoms += vals

    # --- Lógica de Chips con Líneas Cuadradas Escalonadas (Anti-colisión) ---
    chip_style = dict(boxstyle="round,pad=0.3,rounding_size=0.6", fc="white", ec="#D1D1DF", lw=1.2)
    max_total = max(totals)
    min_dist = max_total * 0.045  # Distancia vertical adaptada a la escala de inversión

    for i, x_val in enumerate(x_pos):
        last_y = -min_dist
        
        # Valor total arriba de la barra
        ax.text(i, totals[i] + max_total * 0.015, f'${totals[i]:.1f}', 
                ha='center', va='bottom', fontweight='bold', fontsize=9, color=C_TEXT, zorder=4)
        
        for j, cat in enumerate(CATEGORIAS):
            val = VALS_DICT[cat][i]
            if val >= 0.1:  # Renderizar chip si existe un valor significativo
                pct = (val / totals[i]) * 100 if totals[i] > 0 else 0
                y_center = bottoms_dict[cat][i] + val / 2
                
                # Prevención de solapamiento
                y_text = max(y_center, last_y + min_dist)
                last_y = y_text
                
                # Desplazamiento exterior horizontal
                x_text = x_val - (width / 2) - 0.12
                x_target = x_val - (width / 2)
                
                # Escalonado sutil para evitar cruce de líneas verticales
                x_elbow = x_text + 0.02 + (j * 0.008)
                
                # Trazo de la línea guía cuadrada (Horizontal -> Vertical -> Horizontal)
                ax.plot([x_text, x_elbow, x_elbow, x_target], 
                        [y_text, y_text, y_center, y_center], 
                        color="#A0A0B0", lw=1.2, zorder=3)
                
                # Colocación de la etiqueta dentro del contenedor blanco
                chip_text = f"{pct:.1f}%"
                ax.annotate(chip_text, xy=(x_text, y_text),
                            ha="right", va="center",
                            bbox=chip_style, color=COLORES_DICT[cat], fontweight='bold', fontsize=8,
                            zorder=4)

    # --- Ejes ---
    ax.set_xticks(x_pos)
    ax.set_xticklabels(years, fontsize=10, fontweight='bold', color=C_TEXT)
    ax.tick_params(axis='x', length=0, pad=8)
    
    ax.set_xlim(-0.8, len(years) - 0.2)  # Margen izquierdo suficiente para los primeros chips
    ax.set_ylim(0, max_total * 1.15)
    ax.set_yticks([])  # Ocultar marcas numéricas del eje Y
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#7c7c7c')
    ax.spines['bottom'].set_linewidth(1)
    
    ax.grid(True, axis='y', color='#d1d1d1', linestyle='-', linewidth=1, zorder=0)

    # --- Encabezado Institucional ---
    fig.text(0.08, 0.92, '   ', fontsize=2, va='center',
             bbox=dict(boxstyle='round,pad=1.6,rounding_size=0.2', facecolor='#4a7d75', edgecolor='none'))
    fig.text(0.095, 0.92, 'Figura A.4.', fontsize=14, fontweight='bold', color=C_TEXT, va='center')
    fig.text(0.17, 0.92, 'Inversión privada en Telecomunicaciones por tipo de inversión', 
               fontsize=14, fontweight='medium', color=C_TEXT, va='center')

    # --- Leyenda ---
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.08),
               ncol=4, frameon=False, prop={'weight': 'bold', 'size': 10}, labelcolor=C_TEXT)

    # --- Pie de página ---
    fig.text(0.08, 0.05, "Fuente:", fontweight='bold', fontsize=8, color=C_TEXT)
    fig.text(0.115, 0.05, "IFT con datos proporcionados por los operadores de telecomunicaciones. Para cada año la inversión se presenta acumulada al mes de diciembre.", fontsize=8, color=C_TEXT)
    fig.text(0.08, 0.03, "Nota:", fontweight='bold', fontsize=8, color=C_TEXT)
    fig.text(0.108, 0.03, "Cifras en miles de millones de pesos (pesos corrientes de cada año). Solo se considera la inversión realizada por operadores de servicios de telecomunicaciones.", fontsize=8, color=C_TEXT)

    plt.subplots_adjust(left=0.10, right=0.92, top=0.85, bottom=0.18)
    
    output_file = output_dir / "Figura_A4.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"Figura guardada en: {output_file}")
    plt.close(fig)

if __name__ == "__main__":
    main()