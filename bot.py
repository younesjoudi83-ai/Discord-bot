import discord
from discord.ext import commands, tasks
import random
import os
import json
import asyncio
import aiohttp
from aiohttp import web
import re
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════
# INTENTS (SÉCURISÉS)
# ══════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════
OWNER_ROLES = ["owner", "co owner"]
MOD_ROLES   = ["owner", "co owner", "admin", "super staff", "Staff ໒꒱ིྀ༝⁺", "Staff test ღ", "Super staff", "Admin"]

SPAM_LIMIT = 5
SPAM_INTERVAL = 5
MUTE_DURATION = 5

DEFAULT_SHOP = {
    "VIP": 500,
    "Casino Pro": 1000,
    "Rôle Chanceux": 300
}

# ══════════════════════════════════════════════════════
# JSON
# ══════════════════════════════════════════════════════
os.makedirs("data", exist_ok=True)

def load(filename, default):
    path = f"data/{filename}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save(filename, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

balances = load("balances", {})
warns = load("warns", {})
shop_items = load("shop", DEFAULT_SHOP)
spam_tracker = {}

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════
def has_any_role(member, roles):
    return any(r.name.lower() in [x.lower() for x in roles] for r in member.roles)

def get_balance(uid):
    balances.setdefault(uid, 100)
    return balances[uid]

def set_balance(uid, amount):
    balances[uid] = max(0, amount)
    save("balances", balances)

def embed_base(title, desc="", color=0x5865F2):
    return discord.Embed(title=title, description=desc, color=color)

# ══════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 🔒 PROTECTION DM
    if not message.guild:
        return

    uid = str(message.author.id)
    gid = str(message.guild.id)

    # 🔥 ANTI SPAM
    now = datetime.utcnow()
    key = f"{gid}_{uid}"

    spam_tracker.setdefault(key, [])
    spam_tracker[key] = [t for t in spam_tracker[key] if (now - t).seconds < SPAM_INTERVAL]
    spam_tracker[key].append(now)

    if len(spam_tracker[key]) >= SPAM_LIMIT:
        if not has_any_role(message.author, MOD_ROLES):
            await message.author.timeout(timedelta(minutes=MUTE_DURATION))
            await message.channel.send(f"⚠️ {message.author.mention} muté pour spam")
            spam_tracker[key] = []
            return

    # 🧠 nettoyage mémoire
    if len(spam_tracker) > 10000:
        spam_tracker.clear()

    await bot.process_commands(message)

# ══════════════════════════════════════════════════════
# COMMANDES
# ══════════════════════════════════════════════════════

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency * 1000)}ms")

# 🎁 DAILY sécurisé
@bot.command()
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    uid = str(ctx.author.id)
    reward = random.randint(50, 150)
    set_balance(uid, get_balance(uid) + reward)

    e = embed_base("🎁 Récompense quotidienne", f"+{reward} 🪙")
    await ctx.send(embed=e)

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Reviens dans {round(error.retry_after/3600,1)}h")

# 💰 BALANCE
@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    e = embed_base("💰 Solde", f"{member.mention} a **{get_balance(uid)}** 🪙")
    await ctx.send(embed=e)

# 🎰 GAMBLE
@bot.command()
async def gamble(ctx, amount: int):
    uid = str(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Montant invalide")

    if amount > get_balance(uid):
        return await ctx.send("❌ Fonds insuffisants")

    if random.choice([True, False]):
        set_balance(uid, get_balance(uid) + amount)
        await ctx.send(f"🎉 +{amount} 🪙")
    else:
        set_balance(uid, get_balance(uid) - amount)
        await ctx.send(f"💀 -{amount} 🪙")

# 🔇 MUTE sécurisé
@bot.command()
async def mute(ctx, member: discord.Member, duration: int = 10):
    if not has_any_role(ctx.author, MOD_ROLES):
        return await ctx.send("❌ Pas la permission")

    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("❌ Rôle trop élevé")

    if ctx.author.top_role <= member.top_role:
        return await ctx.send("❌ Tu ne peux pas agir sur ce membre")

    await member.timeout(timedelta(minutes=duration))
    await ctx.send(f"🔇 {member.mention} muté {duration} min")

# 👢 KICK sécurisé
@bot.command()
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES):
        return await ctx.send("❌ Pas la permission")

    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("❌ Rôle trop élevé")

    if ctx.author.top_role <= member.top_role:
        return await ctx.send("❌ Tu ne peux pas agir sur ce membre")

    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} expulsé")

# 🔨 BAN sécurisé
@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES):
        return await ctx.send("❌ Pas la permission")

    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("❌ Rôle trop élevé")

    if ctx.author.top_role <= member.top_role:
        return await ctx.send("❌ Tu ne peux pas agir sur ce membre")

    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} banni")

# 🔓 UNBAN corrigé
@bot.command()
async def unban(ctx, *, username):
    bans = [entry async for entry in ctx.guild.bans()]
    for ban_entry in bans:
        if username.lower() in str(ban_entry.user).lower():
            await ctx.guild.unban(ban_entry.user)
            return await ctx.send(f"✅ {username} débanni")

    await ctx.send("❌ Introuvable")

# 🧹 CLEAR
@bot.command()
async def clear(ctx, amount: int):
    if not has_any_role(ctx.author, MOD_ROLES):
        return await ctx.send("❌ Pas la permission")

    await ctx.channel.purge(limit=amount + 1)

# ══════════════════════════════════════════════════════
# ERREURS GLOBALES
# ══════════════════════════════════════════════════════
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Erreur dans {event}:", args, kwargs)

# ══════════════════════════════════════════════════════
# WEB SERVER (RAILWAY)
# ══════════════════════════════════════════════════════
async def health(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 3000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
async def main():
    async with bot:
        await start_web()

        token = os.environ.get("Discordtoken")
        if not token:
            raise ValueError("❌ Token manquant")

        await bot.start(token)

asyncio.run(main())
