import discord
from discord.ext import commands, tasks
import random
import os
import json
import asyncio
import aiohttp
from aiohttp import web
import re
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════
OWNER_ROLES = ["owner", "co owner"]
MOD_ROLES   = ["owner", "co owner", "admin", "super staff", "Staff ໒꒱ིྀ༝⁺", "Staff test ღ", "Super staff", "Admin"]

SPAM_LIMIT     = 5    # messages
SPAM_INTERVAL  = 5    # secondes
MUTE_DURATION  = 5    # minutes (anti-spam)

DEFAULT_SHOP = {
    "VIP": 500,
    "Casino Pro": 1000,
    "Rôle Chanceux": 300
}

CHARACTERS = [
    ("Naruto", "⭐⭐⭐", "🦊"), ("Goku", "⭐⭐⭐⭐⭐", "🐉"),
    ("Luffy", "⭐⭐⭐", "🍖"), ("Ichigo", "⭐⭐⭐", "⚔️"),
    ("Levi", "⭐⭐⭐⭐", "🗡️"), ("Eren", "⭐⭐⭐", "🔑"),
    ("Sakura", "⭐⭐", "🌸"), ("Hinata", "⭐⭐", "💜"),
    ("Gojo", "⭐⭐⭐⭐⭐", "♾️"), ("Itachi", "⭐⭐⭐⭐⭐", "🌙"),
    ("Zoro", "⭐⭐⭐⭐", "⚔️"), ("Kakashi", "⭐⭐⭐⭐", "📖"),
    ("Rem", "⭐⭐⭐", "💙"), ("Zero Two", "⭐⭐⭐⭐", "🌹"),
    ("Mikasa", "⭐⭐⭐⭐", "🧣"), ("Killua", "⭐⭐⭐⭐", "⚡"),
    ("Nezuko", "⭐⭐⭐", "🌸"), ("Tanjiro", "⭐⭐⭐", "💧"),
    ("Edward", "⭐⭐⭐", "⚗️"), ("Vegeta", "⭐⭐⭐⭐", "👑"),
]

# ══════════════════════════════════════════════════════
#  PERSISTANCE JSON
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

# ── Données en mémoire ──────────────────────────────
balances      = load("balances", {})
warns         = load("warns", {})
shop_items    = load("shop", DEFAULT_SHOP)
cards         = load("cards", {})
auto_roles    = load("auto_roles", {})
reaction_roles= load("reaction_roles", {})
auto_responses= load("auto_responses", {})
word_filter   = load("word_filter", {})
link_filter   = load("link_filter", {})
spam_tracker  = {}   # en mémoire uniquement
snipe_cache   = {}   # en mémoire uniquement
reminders     = []   # en mémoire uniquement
loto_tickets  = load("loto", {})
last_roll     = load("last_roll", {})

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

def color_ok():   return 0x57F287
def color_ban():  return 0xED4245
def color_warn(): return 0xFEE75C
def color_info(): return 0x5865F2
def color_gold(): return 0xF1C40F
def color_purple(): return 0x9B59B6

def foot(ctx):
    return ctx.author.display_name, ctx.author.display_avatar.url

def embed_base(title, desc=None, color=0x5865F2):
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
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="le serveur 👁️"
    ))
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
    if user.bot:
        return
    key = str(reaction.message.id)
    if key in reaction_roles:
        emoji = str(reaction.emoji)
        if emoji in reaction_roles[key]:
            role = discord.utils.get(user.guild.roles, name=reaction_roles[key][emoji])
            if role:
                await user.add_roles(role)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return
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
    if message.author.bot:
        return

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
#  MODÉRATION
# ══════════════════════════════════════════════════════
@bot.command()
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    await member.kick(reason=reason)
    e = embed_base("👢 Membre expulsé", color=color_warn())
    e.add_field(name="Membre", value=member.mention)
    e.add_field(name="Par", value=ctx.author.mention)
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)
    log = embed_base("👢 Kick", color=color_warn())
    log.add_field(name="Membre", value=f"{member} ({member.id})")
    log.add_field(name="Modérateur", value=str(ctx.author))
    log.add_field(name="Raison", value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    await member.ban(reason=reason)
    e = embed_base("🔨 Membre banni", color=color_ban())
    e.add_field(name="Membre", value=member.mention)
    e.add_field(name="Par", value=ctx.author.mention)
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)
    log = embed_base("🔨 Ban", color=color_ban())
    log.add_field(name="Membre", value=f"{member} ({member.id})")
    log.add_field(name="Modérateur", value=str(ctx.author))
    log.add_field(name="Raison", value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
async def unban(ctx, *, username):
    if not has_any_role(ctx.author, OWNER_ROLES): return await no_perm(ctx)
    bans = [entry async for entry in ctx.guild.bans()]
    for ban_entry in bans:
        if str(ban_entry.user) == username:
            await ctx.guild.unban(ban_entry.user)
            e = embed_base("✅ Membre débanni", f"**{username}** a été débanni.", color_ok())
            e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=e)
    await ctx.send(embed=embed_base("❌ Introuvable", f"Aucun ban pour **{username}**.", color_ban()))

@bot.command()
async def mute(ctx, member: discord.Member, duration: int = 10, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    await member.timeout(timedelta(minutes=duration), reason=reason)
    e = embed_base("🔇 Membre muté", color=color_warn())
    e.add_field(name="Membre", value=member.mention)
    e.add_field(name="Par", value=ctx.author.mention)
    e.add_field(name="Durée", value=f"{duration} min")
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)
    log = embed_base("🔇 Mute", color=color_warn())
    log.add_field(name="Membre", value=f"{member} ({member.id})")
    log.add_field(name="Durée", value=f"{duration} min")
    log.add_field(name="Modérateur", value=str(ctx.author))
    log.add_field(name="Raison", value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
async def unmute(ctx, member: discord.Member):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    await member.timeout(None)
    e = embed_base("🔊 Membre démuté", f"{member.mention} peut à nouveau écrire.", color_ok())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def clear(ctx, amount: int):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    await ctx.channel.purge(limit=amount + 1)
    e = embed_base("🧹 Messages supprimés", f"**{amount}** messages effacés.", color_info())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e, delete_after=4)

@bot.command()
async def role(ctx, member: discord.Member, r: discord.Role):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    if r in member.roles:
        await member.remove_roles(r)
        action, color = "retiré ➖", color_warn()
    else:
        await member.add_roles(r)
        action, color = "ajouté ➕", color_ok()
    e = embed_base("🎭 Rôle modifié", color=color)
    e.add_field(name="Membre", value=member.mention)
    e.add_field(name="Rôle", value=r.mention)
    e.add_field(name="Action", value=action)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ── Avertissements ────────────────────────────────
@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    gid, uid = str(ctx.guild.id), str(member.id)
    warns.setdefault(gid, {}).setdefault(uid, [])
    warns[gid][uid].append({"reason": reason, "by": str(ctx.author), "date": datetime.utcnow().strftime("%d/%m/%Y")})
    save("warns", warns)
    count = len(warns[gid][uid])
    e = embed_base(f"⚠️ Avertissement #{count}", color=color_warn())
    e.add_field(name="Membre", value=member.mention)
    e.add_field(name="Par", value=ctx.author.mention)
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)
    if count >= 3:
        await member.kick(reason="3 avertissements accumulés")
        await ctx.send(embed=embed_base("👢 Kick automatique", f"{member.mention} a été expulsé après 3 avertissements.", color_ban()))
    log = embed_base(f"⚠️ Warn #{count}", color=color_warn())
    log.add_field(name="Membre", value=f"{member} ({member.id})")
    log.add_field(name="Modérateur", value=str(ctx.author))
    log.add_field(name="Raison", value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
async def warnings(ctx, member: discord.Member):
    gid, uid = str(ctx.guild.id), str(member.id)
    user_warns = warns.get(gid, {}).get(uid, [])
    e = embed_base(f"📋 Avertissements de {member.display_name}", color=color_warn())
    e.set_thumbnail(url=member.display_avatar.url)
    if not user_warns:
        e.description = "Aucun avertissement."
    else:
        for i, w in enumerate(user_warns, 1):
            e.add_field(name=f"#{i} — {w['date']}", value=f"Raison : {w['reason']}\nPar : {w['by']}", inline=False)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def clearwarns(ctx, member: discord.Member):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    gid, uid = str(ctx.guild.id), str(member.id)
    if gid in warns and uid in warns[gid]:
        warns[gid][uid] = []
        save("warns", warns)
    e = embed_base("✅ Avertissements effacés", f"Tous les warns de {member.mention} ont été supprimés.", color_ok())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ── Auto-role ─────────────────────────────────────
@bot.command()
async def autorole(ctx, action: str, *, role_name: str = None):
    if not has_any_role(ctx.author, OWNER_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    if action == "set" and role_name:
        auto_roles[gid] = role_name
        save("auto_roles", auto_roles)
        await ctx.send(embed=embed_base("✅ Auto-role défini", f"Les nouveaux membres recevront **{role_name}**.", color_ok()))
    elif action == "remove":
        auto_roles.pop(gid, None)
        save("auto_roles", auto_roles)
        await ctx.send(embed=embed_base("✅ Auto-role supprimé", "Plus aucun rôle automatique.", color_ok()))
    else:
        await ctx.send(embed=embed_base("ℹ️ Usage", "`!autorole set <nom_rôle>` ou `!autorole remove`", color_info()))

# ── Rôles réactifs ────────────────────────────────
@bot.command()
async def reactionrole(ctx, message_id: int, emoji: str, *, role_name: str):
    if not has_any_role(ctx.author, OWNER_ROLES): return await no_perm(ctx)
    key = str(message_id)
    reaction_roles.setdefault(key, {})[emoji] = role_name
    save("reaction_roles", reaction_roles)
    msg = await ctx.channel.fetch_message(message_id)
    await msg.add_reaction(emoji)
    e = embed_base("✅ Rôle réactif ajouté", color=color_ok())
    e.add_field(name="Emoji", value=emoji)
    e.add_field(name="Rôle", value=role_name)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════════════
@bot.command()
async def ping(ctx):
    e = embed_base("🏓 Pong !", f"Latence : **{round(bot.latency * 1000)}ms**", color_info())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    e = embed_base(f"👤 {member.display_name}", color=color_info())
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Pseudo", value=str(member))
    e.add_field(name="ID", value=str(member.id))
    e.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "?")
    e.add_field(name="Compte créé le", value=member.created_at.strftime("%d/%m/%Y"))
    e.add_field(name="Rôles", value=" ".join(roles) if roles else "Aucun", inline=False)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    e = embed_base(f"🏠 {g.name}", color=color_info())
    if g.icon:
        e.set_thumbnail(url=g.icon.url)
    e.add_field(name="Propriétaire", value=str(g.owner))
    e.add_field(name="Membres", value=str(g.member_count))
    e.add_field(name="Salons", value=str(len(g.channels)))
    e.add_field(name="Rôles", value=str(len(g.roles)))
    e.add_field(name="Créé le", value=g.created_at.strftime("%d/%m/%Y"))
    e.add_field(name="Niveau boost", value=str(g.premium_tier))
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def snipe(ctx):
    data = snipe_cache.get(ctx.channel.id)
    if not data:
        return await ctx.send(embed=embed_base("🔍 Snipe", "Aucun message supprimé récemment.", color_info()))
    e = embed_base("🔍 Message supprimé", data["content"], color_warn())
    e.set_author(name=data["author"], icon_url=data["avatar"])
    e.set_footer(text=f"Supprimé à {data['time']}")
    await ctx.send(embed=e)

@bot.command()
async def remind(ctx, duration: str, *, message: str):
    units = {"s": 1, "m": 60, "h": 3600}
    unit = duration[-1]
    if unit not in units:
        return await ctx.send(embed=embed_base("❌ Format invalide", "Utilise : `!remind 10m message` (s/m/h)", color_ban()))
    try:
        amount = int(duration[:-1])
    except ValueError:
        return await ctx.send(embed=embed_base("❌ Nombre invalide", "Exemple : `!remind 30m Faire la vaisselle`", color_ban()))
    delta = timedelta(seconds=amount * units[unit])
    reminders.append({
        "user_id": ctx.author.id,
        "channel_id": ctx.channel.id,
        "message": message,
        "time": datetime.utcnow() + delta
    })
    e = embed_base("⏰ Rappel enregistré", f"Je te rappellerai dans **{duration}** :\n{message}", color_info())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def sondage(ctx, *, question: str):
    e = embed_base("📊 Sondage", question, color_purple())
    e.set_footer(text=f"Sondage par {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=e)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

# ── Réponses automatiques ─────────────────────────
@bot.command()
async def autoresponse(ctx, action: str, trigger: str = None, *, response: str = None):
    if not has_any_role(ctx.author, OWNER_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    auto_responses.setdefault(gid, {})
    if action == "add" and trigger and response:
        auto_responses[gid][trigger] = response
        save("auto_responses", auto_responses)
        await ctx.send(embed=embed_base("✅ Réponse ajoutée", f"`{trigger}` → {response}", color_ok()))
    elif action == "remove" and trigger:
        auto_responses[gid].pop(trigger, None)
        save("auto_responses", auto_responses)
        await ctx.send(embed=embed_base("✅ Réponse supprimée", f"`{trigger}` retiré.", color_ok()))
    else:
        await ctx.send(embed=embed_base("ℹ️ Usage", "`!autoresponse add <mot> <réponse>` ou `!autoresponse remove <mot>`", color_info()))

# ── Filtres ───────────────────────────────────────
@bot.command()
async def addword(ctx, *, word: str):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    word_filter.setdefault(gid, [])
    if word not in word_filter[gid]:
        word_filter[gid].append(word.lower())
        save("word_filter", word_filter)
    await ctx.send(embed=embed_base("✅ Mot ajouté", f"`{word}` sera désormais filtré.", color_ok()))

@bot.command()
async def removeword(ctx, *, word: str):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    if gid in word_filter and word.lower() in word_filter[gid]:
        word_filter[gid].remove(word.lower())
        save("word_filter", word_filter)
    await ctx.send(embed=embed_base("✅ Mot retiré", f"`{word}` n'est plus filtré.", color_ok()))

@bot.command()
async def linkfilter(ctx, action: str):
    if not has_any_role(ctx.author, MOD_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    if action == "on":
        link_filter[gid] = True
        save("link_filter", link_filter)
        await ctx.send(embed=embed_base("✅ Filtre liens activé", "Les liens seront supprimés automatiquement.", color_ok()))
    elif action == "off":
        link_filter[gid] = False
        save("link_filter", link_filter)
        await ctx.send(embed=embed_base("✅ Filtre liens désactivé", color=color_ok()))

# ══════════════════════════════════════════════════════
#  ÉCONOMIE / CASINO
# ══════════════════════════════════════════════════════
@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    e = embed_base("💰 Solde", color=color_gold())
    e.add_field(name="Compte", value=member.mention)
    e.add_field(name="Solde", value=f"**{get_balance(uid)}** 🪙")
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    reward = random.randint(50, 150)
    set_balance(uid, get_balance(uid) + reward)
    e = embed_base("🎁 Récompense quotidienne", f"Tu as reçu **+{reward}** 🪙 !", color_gold())
    e.add_field(name="Nouveau solde", value=f"**{get_balance(uid)}** 🪙")
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def gamble(ctx, amount: int):
    uid = str(ctx.author.id)
    if amount <= 0:
        return await ctx.send(embed=embed_base("⚠️ Montant invalide", "La mise doit être > 0.", color_warn()))
    if amount > get_balance(uid):
        return await ctx.send(embed=embed_base("💸 Fonds insuffisants", f"Tu n'as que **{get_balance(uid)}** 🪙.", color_ban()))
    win = random.choice([True, False])
    if win:
        set_balance(uid, get_balance(uid) + amount)
        e = embed_base("🎉 Victoire !", f"Tu gagnes **+{amount}** 🪙 !", color_ok())
    else:
        set_balance(uid, get_balance(uid) - amount)
        e = embed_base("💀 Défaite !", f"Tu perds **-{amount}** 🪙...", color_ban())
    e.add_field(name="Nouveau solde", value=f"**{get_balance(uid)}** 🪙")
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    uid, tid = str(ctx.author.id), str(member.id)
    if amount <= 0:
        return await ctx.send(embed=embed_base("⚠️ Montant invalide", color=color_warn()))
    if amount > get_balance(uid):
        return await ctx.send(embed=embed_base("💸 Fonds insuffisants", color=color_ban()))
    set_balance(uid, get_balance(uid) - amount)
    set_balance(tid, get_balance(tid) + amount)
    e = embed_base("💸 Transfert effectué", color=color_ok())
    e.add_field(name="De", value=ctx.author.mention)
    e.add_field(name="À", value=member.mention)
    e.add_field(name="Montant", value=f"**{amount}** 🪙")
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def top(ctx):
    sorted_bal = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    e = embed_base("🏆 Classement des plus riches", color=color_gold())
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (uid, bal) in enumerate(sorted_bal):
        medal = medals[i] if i < 3 else f"`#{i+1}`"
        try:
            user = bot.get_user(int(uid)) or await bot.fetch_user(int(uid))
            name = user.display_name
        except Exception:
            name = f"Utilisateur {uid}"
        lines.append(f"{medal} **{name}** — {bal} 🪙")
    e.description = "\n".join(lines) if lines else "Aucune donnée."
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ── Boutique ─────────────────────────────────────
@bot.command()
async def shop(ctx):
    e = embed_base("🛒 Boutique", color=color_purple())
    for item, price in shop_items.items():
        e.add_field(name=item, value=f"**{price}** 🪙", inline=True)
    e.set_footer(text="!buy <item> pour acheter")
    await ctx.send(embed=e)

@bot.command()
async def buy(ctx, *, item: str):
    uid = str(ctx.author.id)
    item_key = next((k for k in shop_items if k.lower() == item.lower()), None)
    if not item_key:
        return await ctx.send(embed=embed_base("❌ Article introuvable", f"**{item}** n'est pas dans la boutique.", color_ban()))
    price = shop_items[item_key]
    if get_balance(uid) < price:
        return await ctx.send(embed=embed_base("💸 Fonds insuffisants", f"Il te faut **{price}** 🪙.", color_ban()))
    set_balance(uid, get_balance(uid) - price)
    role = discord.utils.get(ctx.guild.roles, name=item_key)
    if role:
        await ctx.author.add_roles(role)
        extra = f"\nLe rôle **{item_key}** t'a été attribué !"
    else:
        extra = ""
    e = embed_base("✅ Achat effectué", f"Tu as acheté **{item_key}** pour **{price}** 🪙.{extra}", color_ok())
    e.add_field(name="Solde restant", value=f"**{get_balance(uid)}** 🪙")
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ── Loto ─────────────────────────────────────────
@bot.command()
async def loto(ctx, tickets: int = 1):
    uid = str(ctx.author.id)
    price = tickets * 10
    if get_balance(uid) < price:
        return await ctx.send(embed=embed_base("💸 Fonds insuffisants", f"{tickets} ticket(s) = **{price}** 🪙.", color_ban()))
    set_balance(uid, get_balance(uid) - price)
    loto_tickets.setdefault(str(ctx.guild.id), {})
    loto_tickets[str(ctx.guild.id)][uid] = loto_tickets[str(ctx.guild.id)].get(uid, 0) + tickets
    save("loto", loto_tickets)
    e = embed_base("🎟️ Tickets achetés", color=color_gold())
    e.add_field(name="Tickets", value=f"**{loto_tickets[str(ctx.guild.id)][uid]}** au total")
    e.add_field(name="Coût", value=f"**{price}** 🪙")
    e.set_footer(text="!drawloto pour tirer le gagnant (Owner)")
    await ctx.send(embed=e)

@bot.command()
async def drawloto(ctx):
    if not has_any_role(ctx.author, OWNER_ROLES): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    pool = loto_tickets.get(gid, {})
    if not pool:
        return await ctx.send(embed=embed_base("❌ Aucun ticket", "Personne n'a acheté de ticket.", color_ban()))
    weighted = [uid for uid, count in pool.items() for _ in range(count)]
    winner_id = random.choice(weighted)
    prize = sum(pool.values()) * 8
    set_balance(winner_id, get_balance(winner_id) + prize)
    loto_tickets[gid] = {}
    save("loto", loto_tickets)
    try:
        winner = bot.get_user(int(winner_id)) or await bot.fetch_user(int(winner_id))
        name = winner.mention
    except Exception:
        name = f"<@{winner_id}>"
    e = embed_base("🎉 Résultat du Loto !", color=color_gold())
    e.description = f"Le gagnant est {name} avec **{prize}** 🪙 !"
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  MINI-JEUX
# ══════════════════════════════════════════════════════
@bot.command(name="ppc")
async def pierre_papier_ciseaux(ctx, choix: str):
    choices = {"pierre": "🪨", "papier": "📄", "ciseaux": "✂️"}
    choix = choix.lower()
    if choix not in choices:
        return await ctx.send(embed=embed_base("❌ Choix invalide", "Utilise : pierre / papier / ciseaux", color_ban()))
    bot_choice = random.choice(list(choices.keys()))
    wins = {"pierre": "ciseaux", "papier": "pierre", "ciseaux": "papier"}
    if choix == bot_choice:
        result, color = "Égalité ! 🤝", color_warn()
    elif wins[choix] == bot_choice:
        result, color = "Tu gagnes ! 🎉", color_ok()
        set_balance(str(ctx.author.id), get_balance(str(ctx.author.id)) + 15)
        result += " (+15 🪙)"
    else:
        result, color = "Tu perds ! 💀", color_ban()
    e = embed_base("🪨📄✂️ Pierre-Papier-Ciseaux", color=color)
    e.add_field(name="Ton choix", value=choices[choix])
    e.add_field(name="Mon choix", value=choices[bot_choice])
    e.add_field(name="Résultat", value=result, inline=False)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def roulette(ctx, couleur: str, mise: int):
    uid = str(ctx.author.id)
    couleur = couleur.lower()
    if couleur not in ["rouge", "noir", "vert"]:
        return await ctx.send(embed=embed_base("❌ Choix invalide", "Choisis : rouge / noir / vert", color_ban()))
    if mise <= 0 or mise > get_balance(uid):
        return await ctx.send(embed=embed_base("💸 Mise invalide", f"Solde : **{get_balance(uid)}** 🪙.", color_ban()))
    result = random.choices(["rouge", "noir", "vert"], weights=[18, 18, 2])[0]
    colors_map = {"rouge": "🔴", "noir": "⚫", "vert": "🟢"}
    multipliers = {"rouge": 2, "noir": 2, "vert": 14}
    if result == couleur:
        gain = mise * multipliers[couleur] - mise
        set_balance(uid, get_balance(uid) + gain)
        e = embed_base(f"🎰 Roulette — {colors_map[result]} {result.capitalize()}", color=color_ok())
        e.description = f"🎉 Tu gagnes **+{gain}** 🪙 !"
    else:
        set_balance(uid, get_balance(uid) - mise)
        e = embed_base(f"🎰 Roulette — {colors_map[result]} {result.capitalize()}", color=color_ban())
        e.description = f"💀 Tu perds **-{mise}** 🪙..."
    e.add_field(name="Ton pari", value=f"{colors_map[couleur]} {couleur.capitalize()}")
    e.add_field(name="Résultat", value=f"{colors_map[result]} {result.capitalize()}")
    e.add_field(name="Nouveau solde", value=f"**{get_balance(uid)}** 🪙")
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def blackjack(ctx, mise: int):
    uid = str(ctx.author.id)
    if mise <= 0 or mise > get_balance(uid):
        return await ctx.send(embed=embed_base("💸 Mise invalide", f"Solde : **{get_balance(uid)}** 🪙.", color_ban()))
    def card():
        c = random.choice(["2","3","4","5","6","7","8","9","10","V","D","R","As"])
        v = {"V":10,"D":10,"R":10,"As":11}.get(c, int(c) if c.isdigit() else 10)
        return c, v
    def hand_value(hand):
        val = sum(v for _, v in hand)
        aces = sum(1 for c, _ in hand if c == "As")
        while val > 21 and aces:
            val -= 10
            aces -= 1
        return val

    player = [card(), card()]
    dealer = [card(), card()]
    pval = hand_value(player)
    dval = hand_value(dealer)
    pfmt = " ".join(c for c, _ in player)
    dfmt = dealer[0][0] + " ?"

    if pval == 21:
        gain = int(mise * 1.5)
        set_balance(uid, get_balance(uid) + gain)
        e = embed_base("🃏 Blackjack — Blackjack !", color=color_gold())
        e.description = f"🎉 Blackjack naturel ! Tu gagnes **+{gain}** 🪙 !"
    elif dval == 21:
        set_balance(uid, get_balance(uid) - mise)
        e = embed_base("🃏 Blackjack — Dealer Blackjack", color=color_ban())
        e.description = f"💀 Le dealer a le Blackjack. Tu perds **-{mise}** 🪙."
    elif pval > 21:
        set_balance(uid, get_balance(uid) - mise)
        e = embed_base("🃏 Blackjack — Bust !", color=color_ban())
        e.description = f"💀 Tu dépasses 21 ! Tu perds **-{mise}** 🪙."
    elif pval > dval or dval > 21:
        set_balance(uid, get_balance(uid) + mise)
        e = embed_base("🃏 Blackjack — Victoire !", color=color_ok())
        e.description = f"🎉 Tu gagnes **+{mise}** 🪙 !"
    elif pval == dval:
        e = embed_base("🃏 Blackjack — Égalité", color=color_warn())
        e.description = "Mise remboursée."
    else:
        set_balance(uid, get_balance(uid) - mise)
        e = embed_base("🃏 Blackjack — Défaite", color=color_ban())
        e.description = f"💀 Le dealer gagne. Tu perds **-{mise}** 🪙."

    e.add_field(name="Ta main", value=f"{pfmt} (={pval})")
    e.add_field(name="Main dealer", value=f"{dfmt}")
    e.add_field(name="Solde", value=f"**{get_balance(uid)}** 🪙", inline=False)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ── Collection de personnages (Mudae-like) ────────
@bot.command()
async def roll(ctx):
    uid = str(ctx.author.id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if last_roll.get(uid) == today:
        return await ctx.send(embed=embed_base("⏳ Roll utilisé", "Tu as déjà roll aujourd'hui. Reviens demain !", color_warn()))
    char = random.choice(CHARACTERS)
    name, rarity, emoji = char
    last_roll[uid] = today
    save("last_roll", last_roll)
    cards.setdefault(uid, [])
    cards[uid].append(name)
    save("cards", cards)
    e = embed_base(f"{emoji} {name}", color=color_purple())
    e.add_field(name="Rareté", value=rarity)
    e.add_field(name="Collection", value=f"**{len(cards[uid])}** personnages")
    e.set_footer(text=f"Roll de {ctx.author.display_name} — 1/jour", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def collection(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    user_cards = cards.get(uid, [])
    e = embed_base(f"📚 Collection de {member.display_name}", color=color_purple())
    e.set_thumbnail(url=member.display_avatar.url)
    if not user_cards:
        e.description = "Aucun personnage. Utilise `!roll` !"
    else:
        counts = {}
        for c in user_cards:
            counts[c] = counts.get(c, 0) + 1
        lines = [f"• {c} x{n}" if n > 1 else f"• {c}" for c, n in counts.items()]
        e.description = "\n".join(lines[:20])
        e.set_footer(text=f"{len(user_cards)} personnage(s) au total")
    await ctx.send(embed=e)

# ── Blagues & Mèmes ───────────────────────────────
@bot.command()
async def blague(ctx):
    async with aiohttp.ClientSession() as session:
        try:
            url = "https://v2.jokeapi.dev/joke/Any?lang=fr&blacklistFlags=nsfw,racist"
            async with session.get(url) as resp:
                data = await resp.json()
            if data["type"] == "single":
                text = data["joke"]
            else:
                text = f"{data['setup']}\n\n||{data['delivery']}||"
            e = embed_base("😂 Blague", text, color_gold())
        except Exception:
            e = embed_base("😂 Blague", "Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon ils tomberaient dans le bateau !", color_gold())
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def meme(ctx):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://meme-api.com/gimme") as resp:
                data = await resp.json()
            e = embed_base(data.get("title", "Mème"), color=color_purple())
            e.set_image(url=data["url"])
            e.set_footer(text=f"r/{data.get('subreddit', 'memes')}")
        except Exception:
            e = embed_base("😅 Erreur", "Impossible de récupérer un mème pour l'instant.", color_ban())
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  HELP
# ══════════════════════════════════════════════════════
@bot.command()
async def help(ctx):
    e = embed_base("📋 Commandes disponibles", color=color_info())
    e.add_field(name="🛡️ Modération — Staff & +",
        value="`!kick` `!ban` `!mute` `!unmute` `!clear` `!role` `!warn` `!warnings` `!clearwarns` `!addword` `!removeword` `!linkfilter`",
        inline=False)
    e.add_field(name="👑 Owner uniquement",
        value="`!unban` `!autorole` `!reactionrole` `!autoresponse` `!drawloto`",
        inline=False)
    e.add_field(name="🎰 Casino",
        value="`!balance` `!daily` `!gamble` `!pay` `!top` `!shop` `!buy` `!loto`",
        inline=False)
    e.add_field(name="🎮 Mini-jeux",
        value="`!ppc <pierre/papier/ciseaux>` `!roulette <rouge/noir/vert> <mise>` `!blackjack <mise>`",
        inline=False)
    e.add_field(name="📚 Collection",
        value="`!roll` (1/jour) `!collection [@membre]`",
        inline=False)
    e.add_field(name="😂 Fun",
        value="`!blague` `!meme`",
        inline=False)
    e.add_field(name="🔧 Utilitaires",
        value="`!ping` `!userinfo` `!serverinfo` `!snipe` `!remind <durée> <message>` `!sondage <question>`",
        inline=False)
    e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  VOL D'EMOJI
# ══════════════════════════════════════════════════════
@bot.command(name="emojis")
@commands.has_permissions(manage_emojis=True)
async def steal_emoji(ctx, emoji: str = None):
    if emoji is None:
        await ctx.send("❌ Utilisation : `!emojis <emoji>`")
        return

    match = re.match(r"<(a?):(\w+):(\d+)>", emoji)
    if not match:
        await ctx.send("❌ Ce n'est pas un emoji personnalisé d'un autre serveur. Envoie un emoji comme ça : `!emojis <:nom:id>`")
        return

    animated = match.group(1) == "a"
    name = match.group(2)
    emoji_id = match.group(3)
    ext = "gif" if animated else "png"
    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("❌ Impossible de télécharger cet emoji.")
                return
            image_data = await resp.read()

    try:
        new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
        e = discord.Embed(
            title="✅ Emoji volé !",
            description=f"{new_emoji} `:{new_emoji.name}:` a été ajouté au serveur !",
            color=0x00ff99
        )
        await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission d'ajouter des emojis.")
    except discord.HTTPException as err:
        await ctx.send(f"❌ Erreur : {err}")

@steal_emoji.error
async def steal_emoji_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu n'as pas la permission de gérer les emojis.")

# ══════════════════════════════════════════════════════
#  SERVEUR WEB (maintien en ligne via UptimeRobot)
# ══════════════════════════════════════════════════════
async def health(request):
    return web.Response(text="Bot en ligne ✅")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 3000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    async with bot:
        await start_web()
        token = os.environ.get("Discordtoken")
        if not token:
            raise ValueError("Discordtoken n'est pas défini.")
        await bot.start(token)

asyncio.run(main())
