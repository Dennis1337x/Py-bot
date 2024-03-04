import discord
from discord.ext import commands
import json

# Load the token from a config.json file
with open('./config.json') as f:
    config = json.load(f)
token = config['token']

intents = discord.Intents.all()
intents.guilds = True
intents.bans = True
intents.members = True
intents.messages = True
intents.reactions = True
intents.dm_messages = True
intents.typing = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Bot is ready!')

async def ban_for_audit_log_action(guild, action_type, reason, restore_action=None):
    try:
        audit_logs = [log async for log in guild.audit_logs(action=action_type)]
        if not audit_logs:
            return
        log_entry = audit_logs[0]
        executor = log_entry.user
        if restore_action:
            await restore_action(log_entry)
        await guild.ban(executor, reason=reason)
        print(f'Banned {executor} for {reason}.')
    except Exception as error:
        print(error)

async def restore_channel(log_entry):
    if log_entry.action == discord.AuditLogAction.channel_delete:
        await log_entry.guild.create_text_channel(name=log_entry.extra.name, category=log_entry.extra.category)
    elif log_entry.action in [discord.AuditLogAction.channel_update, discord.AuditLogAction.channel_create]:
        channel = log_entry.target
        await channel.edit(name=log_entry.before.name)

async def restore_role(log_entry):
    if log_entry.action == discord.AuditLogAction.role_delete:
        await log_entry.guild.create_role(name=log_entry.extra.name, permissions=log_entry.extra.permissions, color=log_entry.extra.color, hoist=log_entry.extra.hoist, mentionable=log_entry.extra.mentionable)
    elif log_entry.action in [discord.AuditLogAction.role_update, discord.AuditLogAction.role_create]:
        role = log_entry.target
        await role.edit(name=log_entry.before.name, permissions=log_entry.before.permissions, color=log_entry.before.color, hoist=log_entry.before.hoist, mentionable=log_entry.before.mentionable)

@bot.event
async def on_guild_role_create(role):
    await ban_for_audit_log_action(role.guild, discord.AuditLogAction.role_create, 'Unauthorized role creation', restore_role)

@bot.event
async def on_guild_role_delete(role):
    await ban_for_audit_log_action(role.guild, discord.AuditLogAction.role_delete, 'Unauthorized role deletion', restore_role)

@bot.event
async def on_guild_role_update(before, after):
    await ban_for_audit_log_action(after.guild, discord.AuditLogAction.role_update, 'Unauthorized role update', restore_role)

@bot.event
async def on_guild_channel_create(channel):
    await ban_for_audit_log_action(channel.guild, discord.AuditLogAction.channel_create, 'Unauthorized channel creation', restore_channel)

@bot.event
async def on_guild_channel_delete(channel):
    await ban_for_audit_log_action(channel.guild, discord.AuditLogAction.channel_delete, 'Unauthorized channel deletion', restore_channel)

@bot.event
async def on_guild_channel_update(before, after):
    await ban_for_audit_log_action(after.guild, discord.AuditLogAction.channel_update, 'Unauthorized channel update', restore_channel)

@bot.event
async def on_guild_emojis_update(guild, before, after):
    await ban_for_audit_log_action(guild, discord.AuditLogAction.emoji_update, 'Unauthorized emoji update')

@bot.event
async def on_member_ban(guild, user):
    await ban_for_audit_log_action(guild, discord.AuditLogAction.ban, 'Unauthorized ban')

@bot.event
async def on_member_kick(user):
    await ban_for_audit_log_action(user.guild, discord.AuditLogAction.kick, 'Unauthorized kick')

@bot.event
async def on_member_update(before, after):
    if before.bot != after.bot and after.bot:
        await ban_for_audit_log_action(after.guild, discord.AuditLogAction.bot_add, 'Unauthorized bot addition')

@bot.event
async def on_guild_update(before, after):
    await ban_for_audit_log_action(after, discord.AuditLogAction.guild_update, 'Unauthorized guild update')

bot.run(token)
