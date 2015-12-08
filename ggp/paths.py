"""File and directory paths for the ggp package."""
import os.path

ggp_module_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(ggp_module_dir, '..'))
prolog_dir = os.path.join(package_dir, 'prolog')
