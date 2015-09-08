"""File and directory paths for the pygdl package."""
import os.path

pygdl_module_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(pygdl_module_dir, '..'))
prolog_dir = os.path.join(package_dir, 'prolog')
