import { Bot, Keyboard } from '@maxhub/max-bot-api';

const token = process.env.MAX_BOT_TOKEN || process.env.BOT_TOKEN;
if (!token) {
  throw new Error('MAX_BOT_TOKEN is not set');
}

const miniAppUrl = process.env.MINIAPP_PUBLIC_URL || 'https://example.org/miniapp';
const bot = new Bot(token);

bot.api.setMyCommands([
  {
    name: 'start',
    description: 'Главное меню',
  },
]);

const mainMenu = Keyboard.inlineKeyboard([
  [Keyboard.button.callback('📱 Открыть приложение', 'open_app')],
  [Keyboard.button.callback('👤 Профиль пациента', 'profile')],
  [Keyboard.button.callback('🧪 Мои анализы', 'results')],
  [Keyboard.button.callback('📄 Последний результат', 'latest')],
  [Keyboard.button.callback('☎️ Помощь', 'help')],
  [Keyboard.button.link('Открыть mini app по ссылке', miniAppUrl)],
]);

const greeting =
  'Здравствуйте! Это бот медицинского центра СМАРТ.\n\n' +
  'Здесь можно посмотреть результаты анализов или открыть мобильное приложение.';

const sendMainMenu = (ctx: { reply: (payload: { text: string; reply_markup?: unknown }) => Promise<unknown> }) =>
  ctx.reply({
    text: greeting,
    reply_markup: mainMenu,
  });

bot.command('start', (ctx) => sendMainMenu(ctx));
bot.on('bot_started', (ctx) => sendMainMenu(ctx));

bot.action('open_app', (ctx) =>
  ctx.reply({
    text: 'Мобильное приложение скоро будет открываться одной кнопкой.',
    reply_markup: mainMenu,
  }),
);

bot.action('profile', (ctx) =>
  ctx.reply({
    text: 'Профиль пациента пока не заполнен. Здесь будет сохранение логина и пароля.',
    reply_markup: mainMenu,
  }),
);

bot.action('results', (ctx) =>
  ctx.reply({
    text: 'Чтобы посмотреть анализы, сначала заполните профиль пациента.',
    reply_markup: mainMenu,
  }),
);

bot.action('latest', (ctx) =>
  ctx.reply({
    text: 'Пока нет готовых результатов.',
    reply_markup: mainMenu,
  }),
);

bot.action('help', (ctx) =>
  ctx.reply({
    text: 'Если возникли вопросы, свяжитесь с медицинским центром СМАРТ.\n+7 (910) 109-39-71',
    reply_markup: mainMenu,
  }),
);

void bot.start();
