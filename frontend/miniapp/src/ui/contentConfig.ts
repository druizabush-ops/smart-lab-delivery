export type MainTab = "home" | "results" | "appointment" | "loyalty" | "services";

export type AppointmentDoctor = {
  id: string;
  fullName: string;
  specialty: string;
  about: string;
  avatarUrl?: string;
  nextSlots: Array<{
    dayLabel: string;
    times: string[];
  }>;
};

export type LoyaltyPromo = {
  id: string;
  title: string;
  subtitle: string;
  accent: "mint" | "violet" | "blue";
};

export type ServiceTreeNode = {
  id: string;
  name: string;
  priceRub?: number;
  children?: ServiceTreeNode[];
};

export type ServiceCategory = {
  id: string;
  name: string;
  servicesCount: number;
  tree: ServiceTreeNode[];
};

export type MiniAppContentConfig = {
  clinicTitle: string;
  clinicSubtitle: string;
  clinicPhone: string;
  clinicHelpText: string;
  clinicHours: string;
  login: {
    title: string;
    subtitle: string;
    loginPlaceholder: string;
    passwordPlaceholder: string;
    submitLabel: string;
    showPasswordLabel: string;
    hidePasswordLabel: string;
    invalidCredentialsMessage: string;
    genericErrorMessage: string;
  };
  navigation: Array<{ tab: MainTab; label: string; iconAsset: string }>;
  home: {
    greetingPrefix: string;
    profileHint: string;
    sections: Array<{
      id: MainTab;
      title: string;
      description: string;
      tone: "mint" | "blue" | "violet" | "sand";
      iconAsset: string;
    }>;
  };
  results: {
    title: string;
    subtitle: string;
    readyLabel: string;
    openLabel: string;
    emptyLabel: string;
  };
  resultDetails: {
    openPdfLabel: string;
    notAvailable: string;
  };
  pdfViewer: {
    titlePrefix: string;
    sendToMax: string;
    share: string;
    save: string;
    copiedForMax: string;
    copiedForShare: string;
  };
  appointment: {
    title: string;
    subtitle: string;
    foundationNote: string;
    doctors: AppointmentDoctor[];
  };
  loyalty: {
    title: string;
    subtitle: string;
    foundationNote: string;
    bonusRub: number;
    discountPercent: number;
    progressPercent: number;
    promos: LoyaltyPromo[];
  };
  services: {
    title: string;
    subtitle: string;
    searchPlaceholder: string;
    searchHint: string;
    foundationNote: string;
    categories: ServiceCategory[];
  };
};

export const miniAppContentConfig: MiniAppContentConfig = {
  clinicTitle: "СМАРТ Медицинский центр",
  clinicSubtitle: "Личный кабинет пациента",
  clinicPhone: "+7 (910) 109-39-71",
  clinicHelpText: "Нужна помощь? Позвоните администратору",
  clinicHours: "с 7:00 до 19:00",
  login: {
    title: "Вход в систему",
    subtitle: "Добро пожаловать в мини приложение медицинского центра СМАРТ",
    loginPlaceholder: "Введите сюда свой логин",
    passwordPlaceholder: "Введите сюда свой пароль",
    submitLabel: "Войти",
    showPasswordLabel: "Показать",
    hidePasswordLabel: "Скрыть",
    invalidCredentialsMessage: "Неверный логин или пароль",
    genericErrorMessage: "Не удалось войти. Попробуйте позже или позвоните администратору.",
  },
  navigation: [
    { tab: "home", label: "Главная", iconAsset: "icon-home.svg" },
    { tab: "results", label: "Анализы", iconAsset: "icon-analyses.svg" },
    { tab: "appointment", label: "Запись", iconAsset: "icon-appointment.svg" },
    { tab: "loyalty", label: "Акции", iconAsset: "icon-promos.svg" },
    { tab: "services", label: "Услуги", iconAsset: "icon-services.svg" },
  ],
  home: {
    greetingPrefix: "Здравствуйте",
    profileHint: "Проверьте и обновите свои данные в профиле при необходимости.",
    sections: [
      { id: "results", title: "Результаты анализов", description: "Просмотр лабораторных исследований и PDF.", tone: "blue", iconAsset: "icon-analyses.svg" },
      { id: "appointment", title: "Запись на прием", description: "Выберите врача и удобное время.", tone: "mint", iconAsset: "icon-appointment.svg" },
      { id: "loyalty", title: "Бонусы и акции", description: "Текущие скидки и персональные предложения.", tone: "violet", iconAsset: "icon-promos.svg" },
      { id: "services", title: "Перечень услуг", description: "Каталог услуг и ориентировочные цены.", tone: "sand", iconAsset: "icon-services.svg" },
    ],
  },
  results: {
    title: "Результаты анализов",
    subtitle: "Список ваших лабораторных исследований",
    readyLabel: "Готово",
    openLabel: "Открыть",
    emptyLabel: "Результатов пока нет.",
  },
  resultDetails: {
    openPdfLabel: "Открыть в PDF",
    notAvailable: "Показатели пока не получены.",
  },
  pdfViewer: {
    titlePrefix: "Исследование №",
    sendToMax: "Отправить в MAX",
    share: "Поделиться",
    save: "Сохранить",
    copiedForMax: "Ссылка на PDF скопирована. Отправьте её в чат MAX.",
    copiedForShare: "Ссылка на PDF скопирована.",
  },
  appointment: {
    title: "Запись на прием",
    subtitle: "Выберите врача и удобное время",
    foundationNote: "Foundation screen: данные врачей и слотов сейчас демо-конфиг.",
    doctors: [
      {
        id: "d1",
        fullName: "Иванова Анна Сергеевна",
        specialty: "Терапевт",
        about: "Прием взрослых",
        nextSlots: [
          { dayLabel: "Сегодня", times: ["10:00", "11:30", "14:00"] },
          { dayLabel: "Завтра", times: ["09:00", "10:30", "12:00"] },
        ],
      },
      {
        id: "d2",
        fullName: "Петров Дмитрий Олегович",
        specialty: "Кардиолог",
        about: "Прием взрослых",
        nextSlots: [
          { dayLabel: "Сегодня", times: ["09:30", "12:00", "15:30"] },
          { dayLabel: "Завтра", times: ["10:00", "11:30", "16:00"] },
        ],
      },
    ],
  },
  loyalty: {
    title: "Бонусы и акции",
    subtitle: "Моя программа лояльности",
    foundationNote: "Foundation screen: бонусная программа сейчас использует mock/config данные.",
    bonusRub: 1250,
    discountPercent: 7,
    progressPercent: 60,
    promos: [
      { id: "p1", title: "Комплексное обследование со скидкой 20%", subtitle: "До 31 мая", accent: "mint" },
      { id: "p2", title: "Скидка 15% на прием невролога", subtitle: "До 15 июня", accent: "violet" },
    ],
  },
  services: {
    title: "Перечень услуг",
    subtitle: "Выберите услугу или найдите нужную",
    searchPlaceholder: "Поиск по услугам",
    searchHint: "Поиск осуществляется по мере ввода",
    foundationNote: "Foundation screen: каталог услуг и цены сейчас из конфигурации.",
    categories: [
      {
        id: "analizy",
        name: "Анализы",
        servicesCount: 1247,
        tree: [
          {
            id: "biohimiya",
            name: "Биохимические исследования",
            children: [
              { id: "ttg", name: "ТТГ (тиреотропный гормон)", priceRub: 250 },
              { id: "t3", name: "Т3 свободный", priceRub: 280 },
              { id: "prolactin", name: "Пролактин", priceRub: 300 },
            ],
          },
          { id: "immuno", name: "Иммунологические исследования", children: [{ id: "ige", name: "IgE общий", priceRub: 460 }] },
        ],
      },
      { id: "therapies", name: "Направления врачей", servicesCount: 312, tree: [{ id: "cardio-consult", name: "Консультация кардиолога", priceRub: 2200 }] },
      { id: "stom", name: "Стоматология", servicesCount: 245, tree: [{ id: "clean", name: "Профессиональная гигиена", priceRub: 3400 }] },
      { id: "uzi", name: "УЗИ", servicesCount: 156, tree: [{ id: "uzi-abd", name: "УЗИ брюшной полости", priceRub: 1800 }] },
      { id: "func", name: "Функциональная диагностика", servicesCount: 178, tree: [{ id: "ecg", name: "ЭКГ", priceRub: 650 }] },
      { id: "gyn", name: "Гинекология", servicesCount: 142, tree: [{ id: "gyn-consult", name: "Консультация гинеколога", priceRub: 2100 }] },
      { id: "lor", name: "ЛОР", servicesCount: 98, tree: [{ id: "lor-consult", name: "Консультация ЛОР", priceRub: 2100 }] },
      { id: "oph", name: "Офтальмология", servicesCount: 86, tree: [{ id: "oph-consult", name: "Консультация офтальмолога", priceRub: 2100 }] },
      { id: "neuro", name: "Неврология", servicesCount: 104, tree: [{ id: "neuro-consult", name: "Консультация невролога", priceRub: 2300 }] },
    ],
  },
};
