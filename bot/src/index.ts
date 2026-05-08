import { Bot, Keyboard } from '@maxhub/max-bot-api';

const token = process.env.MAX_BOT_TOKEN || process.env.BOT_TOKEN;
if (!token) {
  throw new Error('MAX_BOT_TOKEN or BOT_TOKEN is required');
}

const miniappUrl = process.env.MINIAPP_PUBLIC_URL ?? 'https://example.org/miniapp';

const bot = new Bot(token);

const mainMenu = Keyboard.inlineKeyboard([
  [Keyboard.button.link('📱 Открыть приложение', miniappUrl)],
  [Keyboard.button.callback('👤 Профиль пациента', 'profile')],
  [Keyboard.button.callback('🧪 Мои анализы', 'results')],
  [Keyboard.button.callback('📄 Последний результат', 'latest')],
  [Keyboard.button.callback('☎️ Помощь', 'help')],
]);

const greeting =
  'Здравствуйте! Это бот медицинского центра СМАРТ.\nЗдесь можно посмотреть результаты анализов или открыть мобильное приложение.';

const setCommands = (instance: unknown): void => {
  const maybe = instance as { setMyCommands?: (commands: Array<{ command: string; description: string }>) => Promise<unknown> | unknown };
  if (typeof maybe.setMyCommands === 'function') {
    void Promise.resolve(
      maybe.setMyCommands([
        { command: 'start', description: 'Открыть главное меню' },
      ]),
    );
  }
};

bot.command('start', async (ctx: any) => {
  await ctx.reply(greeting, { reply_markup: mainMenu });
});

bot.on('bot_started', async (ctx: any) => {
  setCommands(bot);
  await ctx.reply(greeting, { reply_markup: mainMenu });
});

bot.action('profile', async (ctx: any) => {
  await ctx.reply('Профиль пациента пока не заполнен. Здесь будет сохранение логина и пароля.');
});

bot.action('results', async (ctx: any) => {
  await ctx.reply('Чтобы посмотреть анализы, сначала заполните профиль пациента.');
});

bot.action('latest', async (ctx: any) => {
  await ctx.reply('Пока нет готовых результатов.');
});

bot.action('help', async (ctx: any) => {
  await ctx.reply('Если возникли вопросы, свяжитесь с медицинским центром СМАРТ.\n+7 (910) 109-39-71');
});

setCommands(bot);
bot.start();
