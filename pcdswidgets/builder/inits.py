from pathlib import Path

import pcdswidgets


def main():
    """
    Backfill generated directories with __init__.py to make them python modules.
    """
    for base_dir in get_generated_top_dirs():
        build_inits(base_dir=base_dir)


def get_generated_top_dirs() -> list[Path]:
    """
    Returns the top-level directories that were originally generated.
    """
    module_dir = Path(pcdswidgets.__file__).parent
    top_dirs = [module_dir / "generated"]
    # Other generated directories are those that mirror the ui folder filetree
    for path in (module_dir / "ui").glob("*"):
        if path.is_dir():
            # There is a generated directory at the top-level of the same name, without "ui"
            new_dir_parts = [part for part in path.parts if part != "ui"]
            top_dirs.append(path.with_segments(*new_dir_parts))
    return top_dirs


def build_inits(base_dir: Path):
    """
    Creates blank __init__.py files wherever they are needed in generated directories.

    This makes Python treat these directories as Python modules.

    Parameters
    ----------
    base_dir : Path
        The directory path that contains generated python files in a nested filetree.
    """
    candidates: set[Path] = set()
    for path in base_dir.rglob("*"):
        if "__pycache__" not in path.parts:
            candidates.add(path.with_name("__init__.py"))
    for cand_path in candidates:
        cand_path.touch()


if __name__ == "__main__":
    main()
