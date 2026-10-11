import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction, TextStyle

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- НАСТРОЙКИ ---
ADMIN_CHANNEL_ID = 1558961259288858624  # ID канала для приема заявок (замените на свой)
PARTY_ROLE_ID = 1556388946970279977     # ID роли партии, которая будет выдаваться при нажатии «Принять»
# -----------------


# Кнопки «Принять» / «Отклонить» для администраторов
class DecisionView(discord.ui.View):
    def __init__(self, applicant: discord.Member):
        super().__init__(timeout=None)
        self.applicant = applicant

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="accept_btn")
    async def accept(self, interaction: Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(PARTY_ROLE_ID)
        
        if role:
            try:
                # Выдаем роль кандидату
                await self.applicant.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("Ошибка: У бота недостаточно прав для выдачи этой роли (подвиньте роль бота выше в списке ролей).", ephemeral=True)
                return

        # Отключаем кнопки после нажатия
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "Заявка ОДОБРЕНА"
        embed.add_field(name="Статус", value=f"Роль успешно выдана! Принял: {interaction.user.mention}", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)
        
        # Уведомляем кандидата в личные сообщения
        try:
            await self.applicant.send(f"Поздравляем! Ваша заявка в партию на сервере **{interaction.guild.name}** была одобрена, вам выдана роль **{role.name}**!")
        except discord.Forbidden:
            pass

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="reject_btn")
    async def reject(self, interaction: Interaction, button: discord.ui.Button):
        # Отключаем кнопки после нажатия
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "Заявка ОТКЛОНЕНА"
        embed.add_field(name="Статус", value=f"Отклонил: {interaction.user.mention}", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

        # Уведомляем кандидата в личные сообщения
        try:
            await self.applicant.send(f"К сожалению, ваша заявка в партию на сервере **{interaction.guild.name}** была отклонена.")
        except discord.Forbidden:
            pass


# Модальное окно анкеты для игрока
class ApplicationModal(discord.ui.Modal, title="Заявка в партию"):
    nickname = discord.ui.TextInput(label="Ваш NickName и CID", placeholder="Ivan_Ivanov | 2ABC", required=True)
    age = discord.ui.TextInput(label="Ваш реальный возраст", placeholder="16", required=True)
    online = discord.ui.TextInput(label="Ваш средний онлайн (часов в день)", placeholder="3-5 часов", required=True)
    about = discord.ui.TextInput(label="Почему хотите именно в нашу партию?", style=TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: Interaction):
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        
        if not admin_channel:
            await interaction.response.send_message("Ошибка: Канал для заявок не найден.", ephemeral=True)
            return

        embed = discord.Embed(title="Новая заявка в партию!", color=discord.Color.blue())
        embed.add_field(name="Кандидат", value=interaction.user.mention, inline=False)
        embed.add_field(name="NickName | CID", value=self.nickname.value, inline=True)
        embed.add_field(name="Возраст", value=self.age.value, inline=True)
        embed.add_field(name="Онлайн", value=self.online.value, inline=True)
        embed.add_field(name="О себе / Причина", value=self.about.value, inline=False)
        
        # Отправляем в админ-канал анкету вместе с кнопками управления
        await admin_channel.send(embed=embed, view=DecisionView(applicant=interaction.user))
        await interaction.response.send_message("Ваша заявка успешно отправлена на рассмотрение!", ephemeral=True)


# Команда для вызова формы
@bot.tree.command(name="anketa", description="Подать заявку на вступление в партию")
async def anketa(interaction: Interaction):
    await interaction.response.send_modal(ApplicationModal())


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Бот {bot.user} успешно запущен!")


bot.run(os.getenv("DISCORD_TOKEN"))