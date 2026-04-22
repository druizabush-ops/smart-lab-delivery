export type HomePlaceholderBlock = {
  key: string;
  title: string;
  subtitle: string;
  tone: "blue" | "mint" | "violet";
};

export type MiniAppContentConfig = {
  appTitle: string;
  appSubtitle: string;
  homeGreetingTitle: string;
  homeGreetingSubtitle: string;
  homeActions: {
    results: string;
    appointments: string;
    profile: string;
  };
  results: {
    title: string;
    emptyState: string;
    openButton: string;
    openPdfButton: string;
    downloadPdfButton: string;
  };
  details: {
    title: string;
    backButton: string;
    indicatorsTitle: string;
    indicatorsEmpty: string;
    openPdfButton: string;
    downloadPdfButton: string;
  };
  pdfViewer: {
    title: string;
    backButton: string;
    logoutButton: string;
    saveButton: string;
    shareButton: string;
    sendToMaxButton: string;
  };
  placeholders: HomePlaceholderBlock[];
};

export const miniAppContentConfig: MiniAppContentConfig = {
  appTitle: "Smart Lab",
  appSubtitle: "Медицинский мини-сервис",
  homeGreetingTitle: "Здравствуйте",
  homeGreetingSubtitle: "Ваши данные и результаты доступны в защищённой сессии.",
  homeActions: {
    results: "Результаты анализов",
    appointments: "Мои записи",
    profile: "Профиль",
  },
  results: {
    title: "Результаты анализов",
    emptyState: "Результатов пока нет.",
    openButton: "Открыть",
    openPdfButton: "Открыть PDF",
    downloadPdfButton: "Скачать PDF",
  },
  details: {
    title: "Карточка результата",
    backButton: "Назад к списку",
    indicatorsTitle: "Показатели",
    indicatorsEmpty: "Показатели пока недоступны.",
    openPdfButton: "Открыть PDF",
    downloadPdfButton: "Скачать PDF",
  },
  pdfViewer: {
    title: "Документ",
    backButton: "Назад",
    logoutButton: "Выйти",
    saveButton: "Сохранить",
    shareButton: "Поделиться",
    sendToMaxButton: "Отправить в MAX",
  },
  placeholders: [
    {
      key: "appointments",
      title: "Мои записи",
      subtitle: "Раздел готовится",
      tone: "blue",
    },
    {
      key: "profile",
      title: "Профиль",
      subtitle: "Персональные данные и настройки",
      tone: "mint",
    },
    {
      key: "support",
      title: "Поддержка",
      subtitle: "Помощь по доступу к результатам",
      tone: "violet",
    },
  ],
};
