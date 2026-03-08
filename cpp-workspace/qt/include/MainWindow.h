#pragma once

#include <QMainWindow>
#include <memory>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
	Q_OBJECT
public:
	MainWindow(QWidget* parent = nullptr);
	~MainWindow();

protected:
	void changeEvent(QEvent* evt) override;

private:
	std::unique_ptr<Ui::MainWindow> ui;
};


// ------ translator ------ //

class Translator
{
	struct Data;
public:
	~Translator();
	static Translator& instance();

	bool load(const QLocale& locale);

private:
	Translator();

private:
	std::unique_ptr<Data> d;
};
