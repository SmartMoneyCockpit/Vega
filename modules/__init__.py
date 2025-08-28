# modules/__init__.py
"""
Make 'modules' a package without eager submodule imports.
Avoids ImportError / circular imports when importing modules.* files.
"""
__all__ = []
