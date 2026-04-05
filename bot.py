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
#  INTENTS ET BOT
# ══════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════════════
#  CONSTANTES & CONFIG
# ══════════════════════════════════════════════════════
OWNER_ROLES = ["owner", "co owner"]
MOD_ROLES   = ["owner", "co owner", "admin", "super staff", "Staff ໒꒱ིྀ༝⁺", "Staff test ღ", "Super staff", "Admin"]

SPAM_LIMIT     = 5
SPAM_INTERVAL  = 5
MUTE_DURATION  = 5  # minutes

DEFAULT_SHOP = {"VIP": 500, "Casino Pro": 1000, "Rôle Chanceux": 300}

CHARACTERS = [
    ("Naruto", "⭐⭐⭐", "🦊"), ("Goku", "⭐⭐⭐⭐⭐", "🐉"), ("Luffy", "⭐⭐⭐", "🍖"), ("Ichigo", "⭐⭐⭐", "⚔️"),
    ("Levi", "⭐⭐⭐⭐", "🗡️"), ("Eren", "⭐⭐⭐", "🔑"), ("Sakura", "⭐⭐", "🌸"), ("Hinata", "⭐⭐", "💜"),
    ("Gojo", "⭐⭐⭐⭐⭐", "♾️"), ("Itachi", "⭐⭐⭐⭐⭐", "🌙"), ("Zoro", "⭐⭐⭐⭐", "⚔️"), ("Kakashi", "⭐⭐⭐⭐", "📖"),
    ("Rem", "⭐⭐⭐", "💙"), ("Zero Two", "⭐⭐⭐⭐", "🌹"), ("Mikasa", "⭐⭐⭐⭐", "🧣"), ("Killua", "⭐⭐⭐⭐", "⚡"),
    ("Nezuko", "⭐⭐⭐", "🌸"), ("Tanjiro", "⭐⭐⭐", "💧"), ("Edward", "⭐⭐⭐", "⚗️"), ("Vegeta", "⭐⭐⭐⭐", "👑"),
]

# ══════════════════════════════════════════════════════
#  PERSISTANCE
# ══════════════════════════════════════════════════════
os.makedirs("data", exist_ok=True)

def load(filename: str, default):
    path = f"data/{filename}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save(filename: str, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

balances       = load("balances", {})
warns          = load("warns", {})
shop_items     = load("shop", DEFAULT_SHOP)
cards          = load("cards", {})
auto_roles     = load("auto_roles", {})
reaction_roles = load("reaction_roles", {})
auto_responses = load("auto_responses", {})
word_filter    = load("word_filter", {})
link_filter    = load("link_filter", {})
spam_tracker   = {}
snipe_cache    = {}
reminders      = []
loto_tickets   = load("loto", {})
last_roll      = load("last_roll", {})

# ══════════════════════════════════════════════════════
#  COULEURS EMBEDS
# ══════════════════════════════════════════════════════
def color_ok():   return 0x57F287
def color_ban():  return 0xED4245
def color_warn(): return 0xFEE75C
def color_info(): return 0x5865F2
def color_gold(): return 0xF1C40F
def color_purple(): return 0x9B59B6
def color_cyan(): return 0x1ABC9C
def color_red(): return 0xE74C3C
def color_blue(): return 0x3498DB

# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════
def has_any_role(member, role_names):
    roles = [r.name.lower() for r in member.roles]
    return any(r.lower() in roles for r in role_names)

def get_balance(uid):
    balances.setdefault(str(uid), 100)
    return balances[str(uid)]

def set_balance(uid, amount):
    balances[str(uid)] = max(0, amount)
    save("balances", balances)

def embed_base(title, desc=None, color=color_info()):
    e = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())
    return e

async def no_perm(ctx):
    e = embed_base("❌ Accès refusé", "Tu n'as pas le rôle requis.", color_ban())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

async def send_log(guild, embed):
    log_channel = discord.utils.get(guild.text_channels, name="mod-logs") or \
                  discord.utils.get(guild.text_channels, name="logs")
    if log_channel:
        await log_channel.send(embed=embed)

# ══════════════════════════════════════════════════════
#  ÉVÉNEMENTS
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="le serveur 👁️"))
    reminder_task.start()
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_member_join(member):
    gid = str(member.guild.id)
    if gid in auto_roles:
        role = discord.utils.get(member.guild.roles, name=auto_roles[gid])
        if role:
            await member.add_roles(role)

@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        snipe_cache[message.channel.id] = {
            "content": message.content,
            "author": str(message.author),
            "avatar": str(message.author.display_avatar.url),
            "time": datetime.utcnow().strftime("%H:%M:%S")
        }

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot: return
    key = str(reaction.message.id)
    if key in reaction_roles:
        emoji = str(reaction.emoji)
        if emoji in reaction_roles[key]:
            role = discord.utils.get(user.guild.roles, name=reaction_roles[key][emoji])
            if role:
                await user.add_roles(role)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot: return
    key = str(reaction.message.id)
    if key in reaction_roles:
        emoji = str(reaction.emoji)
        if emoji in reaction_roles[key]:
            role = discord.utils.get(user.guild.roles, name=reaction_roles[key][emoji])
            if role:
                await user.remove_roles(role)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        uid = str(member.id)
        reward = random.randint(5, 20)
        set_balance(uid, get_balance(uid) + reward)

@bot.event
async def on_message(message):
    if message.author.bot: return

    gid = str(message.guild.id) if message.guild else None
    content = message.content.lower()

    # ── Filtre mots interdits ──
    if gid and gid in word_filter:
        for word in word_filter[gid]:
            if word.lower() in content:
                await message.delete()
                e = embed_base("🚫 Message supprimé", f"{message.author.mention}, ce mot est interdit.", color_ban())
                await message.channel.send(embed=e, delete_after=4)
                return

    # ── Filtre liens ──
    if gid and gid in link_filter and link_filter[gid]:
        url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
        if url_pattern.search(message.content):
            if not has_any_role(message.author, MOD_ROLES):
                await message.delete()
                e = embed_base("🔗 Lien supprimé", f"{message.author.mention}, les liens ne sont pas autorisés.", color_ban())
                await message.channel.send(embed=e, delete_after=4)
                return

    # ── Anti-spam ──
    if gid:
        uid = str(message.author.id)
        now = datetime.utcnow()
        key = f"{gid}_{uid}"
        spam_tracker.setdefault(key, [])
        spam_tracker[key] = [t for t in spam_tracker[key] if (now - t).seconds < SPAM_INTERVAL]
        spam_tracker[key].append(now)
        if len(spam_tracker[key]) >= SPAM_LIMIT:
            if not has_any_role(message.author, MOD_ROLES):
                spam_tracker[key] = []
                await message.author.timeout(timedelta(minutes=MUTE_DURATION), reason="Anti-spam")
                e = embed_base("⚠️ Anti-Spam", f"{message.author.mention} a été muté {MUTE_DURATION} min pour spam.", color_warn())
                await message.channel.send(embed=e)
                return

    # ── Réponses automatiques ──
    if gid and gid in auto_responses:
        for trigger, response in auto_responses[gid].items():
            if trigger.lower() in content:
                await message.channel.send(response)
                break

    await bot.process_commands(message)

# ══════════════════════════════════════════════════════
#  TÂCHE : RAPPELS
# ══════════════════════════════════════════════════════
@tasks.loop(seconds=30)
async def reminder_task():
    now = datetime.utcnow()
    for r in reminders[:]:
        if now >= r["time"]:
            channel = bot.get_channel(r["channel_id"])
            user = bot.get_user(r["user_id"])
            if channel and user:
                e = embed_base("⏰ Rappel !", f"{user.mention} — {r['message']}", color_info())
                await channel.send(embed=e)
            reminders.remove(r)

# ══════════════════════════════════════════════════════
#  COMMANDE HELP ÉLÉGANTE
# ══════════════════════════════════════════════════════
@bot.command()
async def help(ctx):
    e = discord.Embed(title="✨ Menu des commandes", color=color_cyan(), timestamp=datetime.utcnow())
    e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    e.set_footer(text=f"Demandé par {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

    categories = {
        "💼 Modération": ["kick", "ban", "mute", "unmute", "warn", "warnings", "clearwarns", "clear", "role", "autorole", "reactionrole", "unban"],
        "💰 Économie": ["balance", "daily", "pay", "top", "gamble", "shop", "buy"],
        "🎲 Jeux & Loto": ["ppc", "roulette", "blackjack", "roll", "collection", "loto", "drawloto", "sondage"],
        "📜 Utilitaires": ["userinfo", "serverinfo", "snipe", "remind", "autoresponse"],
        "🚫 Filtres": ["addword", "removeword", "linkfilter"]
    }

    for cat, cmds in categories.items():
        e.add_field(name=cat, value=" | ".join(f"`!{c}`" for c in cmds), inline=False)

    await ctx.send(embed=e)
