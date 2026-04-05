import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio

# ------------------------
# CONFIGURATION
# ------------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True  # nécessaire pour mute, kick, ban

bot = commands.Bot(command_prefix='!', intents=intents)

# ------------------------
# VARIABLES MEMOIRE
# ------------------------
spam_tracker = {}  # Pour éviter le spam
reminders = {}     # Pour les rappels
warns = {}         # Pour suivre les avertissements

# ------------------------
# EVENTS
# ------------------------
@bot.event
async def on_ready():
    print(f'{bot.user} connecté !')

@bot.event
async def on_message(message):
    # Protection DM
    if not message.guild:
        return
    # Filtre simple anti-spam
    user_id = message.author.id
    if user_id in spam_tracker:
        spam_tracker[user_id] += 1
        if spam_tracker[user_id] > 5:
            await message.channel.send(f"{message.author.mention} Stop le spam !")
            spam_tracker[user_id] = 0
    else:
        spam_tracker[user_id] = 1

    await bot.process_commands(message)

# ------------------------
# COMMANDES DE MODERATION
# ------------------------
def can_manage(ctx, target):
    return ctx.author.top_role > target.top_role and ctx.guild.me.top_role > target.top_role

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if not can_manage(ctx, member):
        return await ctx.send("Vous ne pouvez pas bannir ce membre.")
    await member.ban(reason=reason)
    await ctx.send(f"{member} a été banni pour : {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_tag):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member_tag.split('#')
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"{user} a été débanni.")
            return
    await ctx.send("Membre non trouvé.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if not can_manage(ctx, member):
        return await ctx.send("Vous ne pouvez pas expulser ce membre.")
    await member.kick(reason=reason)
    await ctx.send(f"{member} a été expulsé pour : {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    if not can_manage(ctx, member):
        return await ctx.send("Vous ne pouvez pas mute ce membre.")
    mute_role = get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)
    await member.add_roles(mute_role)
    await ctx.send(f"{member} a été mute pour : {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    mute_role = get(ctx.guild.roles, name="Muted")
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(f"{member} a été unmute.")
    else:
        await ctx.send("Ce membre n'est pas mute.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.id not in warns:
        warns[member.id] = []
    warns[member.id].append(reason)
    await ctx.send(f"{member} a été averti : {reason}")

@bot.command()
async def infractions(ctx, member: discord.Member):
    user_warns = warns.get(member.id, [])
    await ctx.send(f"{member} a {len(user_warns)} avertissement(s): {user_warns}")

# ------------------------
# COMMANDES UTILITAIRES
# ------------------------
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ! {round(bot.latency * 1000)}ms")

@bot.command()
async def emojis(ctx):
    """Liste tous les emojis du serveur"""
    emojis_list = " ".join([str(e) for e in ctx.guild.emojis])
    if not emojis_list:
        emojis_list = "Aucun emoji sur ce serveur."
    await ctx.send(emojis_list)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"{guild.name}", description=f"Informations du serveur", color=discord.Color.blue())
    embed.add_field(name="Membres", value=guild.member_count)
    embed.add_field(name="Rôles", value=len(guild.roles))
    embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"))
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member):
    embed = discord.Embed(title=f"{member}", color=discord.Color.green())
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Rôles", value=", ".join([r.name for r in member.roles if r.name != "@everyone"]))
    embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y"))
    await ctx.send(embed=embed)

# ------------------------
# ECONOMIE / JEUX
# ------------------------
# Exemple simple de !roll
@bot.command()
async def roll(ctx, sides: int = 6):
    import random
    await ctx.send(f"{ctx.author.mention} a roulé un {random.randint(1, sides)} !")

# ------------------------
# DEMARRAGE DU BOT
# ------------------------
bot.run(os.environ['TOKEN'])  # Token dans variable secrète
