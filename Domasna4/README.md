1. Singleton шаблон

Локација: python_filters/database_connector.py
Намена: Обезбедување една единствена глобална инстанца на конекторот кон базата на податоци.
Пример:

_connector = None

def get_connector() -> DatabaseConnector:
    global _connector
    if _connector is None:
        _connector = DatabaseConnector()
    return _connector


2. Strategy шаблон (имплицитно)

Локација: TechnicalAnalysisServiceImpl
Намена: Имплементација на различни стратегии за пресметка на технички индикатори.
Пример:
Методи како calculateOscillators() и calculateMovingAverages() користат различни алгоритми (RSI, MACD, Stochastic, ADX, CCI).


3. Template Method шаблон

Локација: Python филтри (Filter1.py, Filter2.py, Filter3.py)
Намена: Дефинирање на стандарден тек на извршување со можност за варијации.
Пример:
Секој филтер ја следи истата структура: поврзување → преземање податоци → обработка → зачувување.


4. Facade шаблон

Локација: Service класи
Намена: Обезбедување поедноставен интерфејс кон комплексни подсистеми.
Пример:
PredictionService ги сокрива деталите за извршување на Python скрипти од контролерите.


5. Builder шаблон

Локација: Python код со BaseBarSeriesBuilder
Намена: Постепена конструкција на комплексни објекти.
Пример:

new BaseBarSeriesBuilder()
    .withName("CryptoData")
    .build();


6. Factory шаблон

Локација: SQLAlchemy sessionmaker
Намена: Креирање на инстанци на сесии кон базата на податоци.
Пример:
sessionmaker(bind=self.engine) создава нови database session објекти.


7. Adapter шаблон (имплицитно)

Локација: PredictionService и LSTMPredictionService
Намена: Адаптација на извршување Python скрипти кон Java service интерфејси.
Пример:
Java сервисите извршуваат Python скрипти и ги парсираат JSON резултатите во соодветни DTO објекти.


8. Observer шаблон

Локација: Spring @Scheduled анотација
Намена: Настанско (event-driven) извршување на задачи.
Пример:
@Scheduled(cron = "0 0 1 * * ?") во PythonFilterService овозможува дневно извршување на задачите.