from IsirPythonTools import *

package_name = 'xde_world_manager'

setup(name='XDE-WorldManager',
	  version='0.1',
	  description='World manager util for xde',
	  author='Soseph',
	  author_email='hak@isir.upmc.fr',
	  package_dir={package_name:'src'},
	  packages=[package_name],
	  cmdclass=cmdclass,

	  script_name=script_name,
	  script_args= script_args
	 )
