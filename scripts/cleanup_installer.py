#!/usr/bin/env python3
"""
Script de Limpieza para el Instalador Syntalix-Orion.

Este módulo proporciona una herramienta de saneamiento para eliminar artefactos, 
archivos de estado y entornos virtuales temporales generados durante el 
proceso de instalación o desarrollo.

Es una operación irreversible diseñada para restablecer el entorno de trabajo 
a un estado limpio.

Funcionalidades:
    - Modo 'Dry-run' para previsualizar los archivos que se eliminarán.
    - Eliminación recursiva de caches de Python (__pycache__).
    - Limpieza de entornos virtuales (.venv, venv).
    - Remoción de archivos de estado (state.json) y logs de Textual.
    - Auditoría y reporte final de archivos procesados.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from typing import List


def collect_targets(root: Path) -> List[Path]:
    targets: List[Path] = []

    # state.json files scattered around
    for p in root.rglob("state.json"):
        targets.append(p)

    # textual logs anywhere
    for p in root.rglob("textual.log"):
        targets.append(p)

    # common venvs
    for vocab in [".venv", "venv", "env"]:
        for p in root.rglob(vocab):
            if p.is_dir():
                targets.append(p)

    # common caches and build artifacts
    for name in ["__pycache__", "pytest_cache", "build", "dist", "logs"]:
        for p in root.rglob(name):
            targets.append(p)

    # deduplicate while preserving order
    seen = set()
    uniq: List[Path] = []
    for t in targets:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq


def remove_path(p: Path) -> bool:
    try:
        if p.is_file() or p.suffix != "":
            p.unlink(missing_ok=True)
        elif p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        print(f"Deleted: {p}")
        return True
    except Exception as e:
        print(f"Failed to delete {p}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Cleanup Syntalix-Orion installer artifacts.")
    parser.add_argument("--root", default=".", help="Root path of the project (default: current directory)")
    parser.add_argument("--yes", action="store_true", help="Assume yes to all confirmations")
    parser.add_argument("--dry-run", action="store_true", help="List what would be removed without deleting")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root path does not exist: {root}")
        sys.exit(2)

    targets = collect_targets(root)
    if not targets:
        print("No removable artifacts found.")
        sys.exit(0)

    print("Identified targets to remove:")
    for t in targets:
        print(f" - {t}")

    if args.dry_run:
        print("\nDry-run complete. No files were removed.")
        sys.exit(0)

    if not args.yes:
        resp = input("Proceed to delete these artifacts? [y/N]: ")
        if resp.strip().lower() not in {"y", "yes"}:
            print("Aborted by user.")
            sys.exit(0)

    # perform deletion
    removed = 0
    failed = 0
    for t in targets:
        if t.exists():
            ok = remove_path(t)
            if ok:
                removed += 1
            else:
                failed += 1

    print("\nCleanup completed.")
    print(f"Removed: {removed}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()
