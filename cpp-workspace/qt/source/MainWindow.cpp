#include "MainWindow.h"
#include "ui/ui_MainWindow.h"

#include <QLibraryInfo>
#include <QTranslator>
#include <vector>

MainWindow::MainWindow(QWidget* parent)
	: QMainWindow{ parent }
	, ui{ new Ui::MainWindow{} }
{
	ui->setupUi(this);
}

MainWindow::~MainWindow() {}

void MainWindow::changeEvent(QEvent* evt)
{
	if (evt->type() == QEvent::LanguageChange)
	{
		ui->retranslateUi(this);
	}

	QMainWindow::changeEvent(evt);
}


// ------ translator ------ //

struct Translator::Data
{
	struct TranslatorInfo
	{
		std::unique_ptr<QTranslator> t;
		QString prefix;
		QString path;
	};

	std::vector<TranslatorInfo> translators;
};

Translator::Translator()
	: d{ new Data{} }
{
	d->translators.emplace_back(
		std::make_unique<QTranslator>(),
		PROJECT_NAME, ":/i18n"
	);
	d->translators.emplace_back(
		std::make_unique<QTranslator>(),
		"qt", QLibraryInfo::path(QLibraryInfo::TranslationsPath)
	);

	load(QLocale{});
}
Translator::~Translator() {}

Translator& Translator::instance()
{
	static Translator translator{};
	return translator;
}

bool Translator::load(const QLocale& locale)
{
	for (auto& info : d->translators)
		qApp->removeTranslator(info.t.get());

	bool ret = true;
	for (auto& info : d->translators)
	{
		bool ok = info.t->load(locale, info.prefix, "_", info.path);
		if (ok) qApp->installTranslator(info.t.get());

		ret &= ok;
	}
	return ret;
}