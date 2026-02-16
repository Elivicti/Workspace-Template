#include "MainWindow.h"
#include "ui/ui_MainWindow.h"

#include <QStatusBar>

MainWindow::MainWindow(QWidget* parent)
	: QMainWindow{ parent }
	, ui{ new Ui::MainWindow{} }
{
	ui->setupUi(this);

}

MainWindow::~MainWindow() {}
