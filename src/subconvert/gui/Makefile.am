# subconvert/gui/Makefile.am

gui_PYTHON = \
	__init__.py \
	DataModel.py \
	Detail.py \
	FileDialogs.py \
	FrameTimeSpinBox.py \
	GuiApp.py \
	MainWindow.py \
	OffsetDialog.py \
	PropertyFileEditor.py \
	SubModel.py \
	SubtitleCommands.py \
	SubtitleTabs.py \
	SubtitleWindow.py \
	ToolBox.py \
	VideoWidget.py

guitools_PYTHON = \
	tools/Details.py \
	tools/History.py \
	tools/Synchronizer.py

guidir = $(datadir)/subconvert/subconvert/gui
guitoolsdir = $(datadir)/subconvert/subconvert/gui/tools

CLEANFILES = *.pyc *.pyo
CLEANFILES += tools/*.pyc tools/*.pyo

clean-local:
	rm -rf __pycache__
