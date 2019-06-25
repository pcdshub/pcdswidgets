# Install the package
$PYTHON setup.py install --single-version-externally-managed --record=record.txt

# Create auxillary
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d
mkdir -p $PREFIX/etc/pcdswidgets

# Create auxiliary vars
DESIGNER_PLUGIN_PATH=$PREFIX/etc/pcdswidgets
DESIGNER_PLUGIN=$DESIGNER_PLUGIN_PATH/pcdswidgets_designer_plugin.py
ACTIVATE=$PREFIX/etc/conda/activate.d/pcdswidgets.sh
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/pcdswidgets.sh

echo "from pcdswidgets.designer import *" >> $DESIGNER_PLUGIN
echo "export PYQTDESIGNERPATH="$DESIGNER_PLUGIN_PATH":\$PYQTDESIGNERPATH" >> $ACTIVATE
echo "unset PYQTDESIGNERPATH" >> $DEACTIVATE

unset DESIGNER_PLUGIN_PATH
unset DESIGNER_PLUGIN
unset ACTIVATE
unset DEACTIVATE
