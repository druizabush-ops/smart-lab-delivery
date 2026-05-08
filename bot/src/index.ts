import { Bot, Keyboard } from '@maxhub/max-bot-api';

const token = process.env.MAX_BOT_TOKEN;
if (!token) {
  throw new Error('MAX_BOT_TOKEN is required');
}

const miniappUrl = process.env.MINIAPP_PUBLIC_URL ?? 'https://example.org/miniapp';

const bot = new Bot({ token });

const mainMenu = Keyboard.inlineKeyboard([
  [Keyboard.button.link('📱 Открыть приложение', miniappUrl)],
  [Keyboard.button.callback('👤 Профиль пациента', 'profile')],
  [Keyboard.button.callback('🧪 Мои анализы', 'results')],
  [Keyboard.button.callback('📄 Последний результат', 'last_result')],
  [Keyboard.button.callback('☎️ Помощь', 'help')],
]);

const greeting = 'Здравствуйте! Это бот медицинского центра СМАРТ.\nЗдесь можно посмотреть результаты анализов или открыть мобильное приложение.';

bot.command('start', async (ctx) => {
  await ctx.answer(greeting, { reply_markup: mainMenu });
});

bot.on('bot_started', async (ctx) => {
  await ctx.answer(greeting, { reply_markup: mainMenu });
});

bot.action('profile', async (ctx) => {
  await ctx.answer('Профиль пациента пока не заполнен.');
});

bot.action('results', async (ctx) => {
  await ctx.answer('Чтобы посмотреть анализы, заполните профиль пациента.');
});

bot.action('last_result', async (ctx) => {
  await ctx.answer('Пока нет готовых результатов.');
});

bot.action('help', async (ctx) => {
  await ctx.answer('Если возникли вопросы, свяжитесь с медицинским центром СМАРТ.\n+7 (910) 109-39-71');
});

bot.start();
