"""Utilities to print plotted data at save time for traceability."""

from __future__ import annotations

from typing import Iterable


def _format_number(value) -> str:
    try:
        return f"{float(value):.6g}"
    except Exception:
        return str(value)


def _iter_line_rows(line) -> Iterable[str]:
    x_data = list(line.get_xdata())
    y_data = list(line.get_ydata())
    for idx, (x_val, y_val) in enumerate(zip(x_data, y_data), start=1):
        yield f"    {idx:>4} | x={_format_number(x_val):>12} | y={_format_number(y_val):>12}"


def _print_axes_data(fig) -> None:
    print("\n=== DATOS PROCESADOS USADOS EN LA GRAFICA ===")
    for ax_idx, ax in enumerate(fig.axes, start=1):
        print(f"\n  [Eje {ax_idx}] title='{ax.get_title()}'")

        lines = ax.get_lines()
        if lines:
            print("  Series de linea:")
            for line_idx, line in enumerate(lines, start=1):
                label = line.get_label()
                print(f"  - Linea {line_idx}: label='{label}'")
                for row in _iter_line_rows(line):
                    print(row)

        containers = ax.containers
        if containers:
            print("  Series de barras:")
            for container_idx, container in enumerate(containers, start=1):
                print(f"  - Contenedor {container_idx}:")
                for bar_idx, patch in enumerate(container, start=1):
                    x_center = patch.get_x() + (patch.get_width() / 2.0)
                    y_top = patch.get_y() + patch.get_height()
                    print(
                        "    "
                        f"{bar_idx:>4} | x={_format_number(x_center):>12} "
                        f"| y={_format_number(y_top):>12} "
                        f"| w={_format_number(patch.get_width()):>10} "
                        f"| h={_format_number(patch.get_height()):>10}"
                    )

    print("=== FIN DATOS GRAFICA ===\n")


def enable_plot_data_logging() -> None:
    """Patch matplotlib Figure.savefig once to print plotted data before writing files."""
    try:
        from matplotlib.figure import Figure
    except Exception:
        return

    if getattr(Figure, "_anuario_savefig_patched", False):
        return

    original_savefig = Figure.savefig

    def patched_savefig(self, *args, **kwargs):
        _print_axes_data(self)
        return original_savefig(self, *args, **kwargs)

    Figure.savefig = patched_savefig
    Figure._anuario_savefig_patched = True
