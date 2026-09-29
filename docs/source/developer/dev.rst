=======================================
Configuring the Development Environment
=======================================

#. Create a virtual environment with conda or use a preexisting environment.
#. Activate the environment. All following steps assume that you are inside this enviornment.
#. Install pydm, pyqt, and pcdsdevices from the conda-forge channel with ``conda install -c conda-forge pydm pyqt pcdsdevices``
#. Clone a copy of pcdswidgets from here ``https://github.com/pcdshub/pcdswidgets``
#. Move into the newly cloned pcdswidgets directory and run ``pip install -e .`` to perform a development install of pcdswidgets.
#. In order to ensure that designer loads the new widgets add the newly cloned pcdswidgets directory to the environment variable ``PYQTDESIGNERPATH``. For example, use ``export PYQTDESIGNERPATH=$PWD:$PYQTDESIGNERPATH`` after cd'ing into your pcdswidgets directory.
#. Setup of the environment is now complete. You should be able to make changes to your newly cloned pcdswidgets directory and see those changes reflected in ``designer``.
