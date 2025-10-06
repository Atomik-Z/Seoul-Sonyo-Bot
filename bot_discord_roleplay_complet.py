
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import asyncio
import os
from datetime import datetime
from typing import Optional

# Configuration du bot
TOKEN = os.environ.get('DISCORD_TOKEN')  # Remplacez par votre token
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# === FONCTIONS UTILITAIRES ===

def init_db():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Table pour les niveaux d'ancienneté des membres
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_levels (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        total_messages INTEGER DEFAULT 0,
        last_message_time REAL DEFAULT 0
    )""")

    # Table pour les personnages de jeu de rôle
    cursor.execute("""CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        character_name TEXT UNIQUE,
        specialty TEXT,
        chant INTEGER DEFAULT 1,
        danse INTEGER DEFAULT 1,
        eloquence INTEGER DEFAULT 1,
        acting INTEGER DEFAULT 1,
        fitness INTEGER DEFAULT 1,
        esthetique INTEGER DEFAULT 1,
        reputation INTEGER DEFAULT 500,
        chant_exp INTEGER DEFAULT 0,
        danse_exp INTEGER DEFAULT 0,
        eloquence_exp INTEGER DEFAULT 0,
        acting_exp INTEGER DEFAULT 0,
        fitness_exp INTEGER DEFAULT 0,
        esthetique_exp INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_levels (user_id)
    )""")

    conn.commit()
    conn.close()

def calc_level_exp(level):
    """Calcule l'XP nécessaire pour atteindre un niveau donné"""
    if level == 1:
        return 200
    base = 200
    for i in range(2, level + 1):
        base = int(base * 1.4)
    return base

def calc_stat_exp(level):
    """Calcule l'XP nécessaire pour les statistiques de personnage"""
    if level == 1:
        return 5000
    base = 5000
    for i in range(2, level + 1):
        base += 120 * i
    return base

def get_seniority_role(level):
    """Retourne le rôle d'ancienneté basé sur le niveau"""
    if 1 <= level <= 9:
        return "newcomer"
    elif 10 <= level <= 19:
        return "rising"
    elif 20 <= level <= 29:
        return "yapper"
    else:
        return "go outside touch some grass"

def get_character_limit(seniority_role):
    """Retourne la limite de personnages basée sur l'ancienneté"""
    limits = {
        "newcomer": 3,
        "rising": 4,
        "yapper": 5,
        "go outside touch some grass": float('inf')
    }
    return limits.get(seniority_role, 3)

# === ÉVÉNEMENTS DU BOT ===

@bot.event
async def on_ready():
    """Événement déclenché quand le bot se connecte"""
    print(f'🤖 {bot.user} est connecté et prêt!')
    init_db()

    # Synchroniser les commandes slash
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synchronisé {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation: {e}")

@bot.event
async def on_message(message):
    """Gère le système d'XP pour chaque message"""
    if message.author.bot:
        return

    # Cooldown pour éviter le spam (optionnel)
    current_time = datetime.now().timestamp()

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    user_id = message.author.id
    username = str(message.author)

    # Récupérer ou créer l'utilisateur
    cursor.execute("SELECT * FROM user_levels WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("""INSERT INTO user_levels 
                         (user_id, username, last_message_time) 
                         VALUES (?, ?, ?)""", (user_id, username, current_time))
        user = (user_id, username, 1, 0, 0, current_time)

    # Ajouter de l'XP aléatoire (3-5 points)
    exp_gain = random.randint(3, 5)
    new_exp = user[3] + exp_gain
    new_total_messages = user[4] + 1
    current_level = user[2]

    # Vérifier les montées de niveau
    new_level = current_level
    level_ups = 0

    while True:
        exp_needed = calc_level_exp(new_level + 1)
        if new_exp >= exp_needed:
            new_level += 1
            new_exp -= exp_needed
            level_ups += 1
        else:
            break

    # Si montée de niveau
    if level_ups > 0:
        # Message de montée de niveau
        if level_ups == 1:
            await message.channel.send(f"🎉 {message.author.mention} a atteint le niveau **{new_level}** !")
        else:
            await message.channel.send(f"🚀 {message.author.mention} a gagné **{level_ups} niveaux** et atteint le niveau **{new_level}** !")

        # Gérer les rôles d'ancienneté
        await update_seniority_roles(message.author, new_level, message.guild)

    # Mettre à jour la base de données
    cursor.execute("""UPDATE user_levels 
                     SET level = ?, exp = ?, total_messages = ?, username = ?, last_message_time = ? 
                     WHERE user_id = ?""",
                   (new_level, new_exp, new_total_messages, username, current_time, user_id))

    conn.commit()
    conn.close()

    await bot.process_commands(message)

async def update_seniority_roles(member, level, guild):
    """Met à jour les rôles d'ancienneté d'un membre"""
    if not guild:
        return

    new_role_name = get_seniority_role(level)
    old_roles = ["newcomer", "rising", "yapper", "go outside touch some grass"]

    # Supprimer les anciens rôles d'ancienneté
    for role_name in old_roles:
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                print(f"❌ Pas de permission pour supprimer le rôle {role_name}")

    # Ajouter le nouveau rôle
    new_role = discord.utils.get(guild.roles, name=new_role_name)
    if new_role:
        try:
            await member.add_roles(new_role)
            print(f"✅ Rôle '{new_role_name}' attribué à {member}")
        except discord.Forbidden:
            print(f"❌ Pas de permission pour attribuer le rôle {new_role_name}")
    else:
        print(f"⚠️ Rôle '{new_role_name}' non trouvé sur le serveur")

# === COMMANDE D'AIDE ===

@bot.tree.command(name="aide", description="Affiche la liste de toutes les commandes disponibles")
async def help_command(interaction: discord.Interaction):
    """Affiche la liste complète des commandes du bot"""
    embed = discord.Embed(
        title="🤖 Guide des Commandes - Bot JdR",
        description="Voici toutes les commandes disponibles pour le bot de jeu de rôle",
        color=0x00d4ff
    )

    # Système de niveaux d'ancienneté
    niveau_commands = """
**`/niveau`** - Vérifiez votre niveau et votre XP
• Affiche votre progression, rang d'ancienneté et statistiques

**`/classement`** - Classement des membres du serveur
• Top 15 des membres les plus actifs avec leurs niveaux
    """
    embed.add_field(name="📊 Système de Niveaux", value=niveau_commands, inline=False)

    # Gestion des personnages
    character_commands = """
**`/creer_personnage <nom>`** - Créer un nouveau personnage
• Interface interactive pour choisir spécialité et bonus

**`/mes_personnages`** - Liste de vos personnages
• Vue d'ensemble de tous vos personnages créés

**`/stats_personnage <nom>`** - Statistiques détaillées
• Voir toutes les stats d'un personnage avec barres de progression

**`/entrainer <nom> <statistique>`** - Entraîner un personnage
• Améliorer une statistique (chant, danse, éloquence, acting, fitness, esthétique)
• Gain de 750-1250 XP + bonus de spécialité

**`/supprimer_personnage <nom>`** - Supprimer un personnage
• Suppression sécurisée avec confirmation obligatoire
    """
    embed.add_field(name="🎭 Gestion des Personnages", value=character_commands, inline=False)

    # Spécialités disponibles
    specialties_info = """
**🎵 Chanteur** - Chant niveau 3
**💃 Danseur** - Danse niveau 3  
**🎭 Acteur** - Acting niveau 3
**📰 Reporter** - Éloquence niveau 3
**💪 Coach** - Fitness niveau 3
**✨ Mannequin** - Esthétique niveau 3
**📚 Étudiant** - +10% XP entraînement
**👨‍🏫 Professeur** - Stat niveau 2 + 5% XP
**⭐ Influenceur** - Réputation 1000
**❓ Autre** - Spécialité personnalisée
    """
    embed.add_field(name="🎯 Spécialités Disponibles", value=specialties_info, inline=False)

    # Système automatique
    auto_system = """
• **+3 à 5 XP** par message envoyé automatiquement
• **Montée de niveau** automatique avec notifications
• **Attribution des rôles** d'ancienneté automatique :
  └ Niveaux 1-9 : **newcomer**
  └ Niveaux 10-19 : **rising** 
  └ Niveaux 20-29 : **yapper**
  └ Niveau 30+ : **go outside touch some grass**
• **Limites de personnages** basées sur l'ancienneté
    """
    embed.add_field(name="⚙️ Système Automatique", value=auto_system, inline=False)

    # Administration (si permissions)
    if interaction.user.guild_permissions.administrator:
        admin_commands = """
**`/admin_reset_user <utilisateur>`** - Reset complet d'un utilisateur
• Supprime niveau, XP, personnages et rôles (Admin seulement)
        """
        embed.add_field(name="🛡️ Commandes d'Administration", value=admin_commands, inline=False)

    # Informations supplémentaires
    embed.add_field(
        name="ℹ️ Formules et Informations",
        value="• **Niveaux d'ancienneté** : p(1)=200, p(n+1)=p(n)×1.4\n"
              "• **Statistiques personnage** : e(1)=5000, e(n+1)=e(n)+(120×(n+1))\n"
              "• **Entraînement** : 750-1250 XP + bonus spécialité\n"
              "• **Base de données SQLite** intégrée pour la persistance\n"
              "• Toutes les actions critiques ont des **confirmations de sécurité**",
        inline=False
    )

    embed.set_footer(text="🎮 Bot JdR • Tapez /aide pour revoir ces commandes à tout moment")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, ephemeral=True)

# === COMMANDES POUR LE SYSTÈME DE NIVEAUX ===

@bot.tree.command(name="niveau", description="Vérifiez votre niveau et votre XP")
async def check_level(interaction: discord.Interaction):
    """Affiche le niveau et l'XP de l'utilisateur"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_levels WHERE user_id = ?", (interaction.user.id,))
    user = cursor.fetchone()

    if not user:
        await interaction.response.send_message("❌ Vous n'avez pas encore envoyé de messages!", ephemeral=True)
        conn.close()
        return

    level = user[2]
    exp = user[3]
    total_messages = user[4]
    exp_needed_next = calc_level_exp(level + 1) - exp
    exp_for_current = calc_level_exp(level)
    seniority_role = get_seniority_role(level)

    embed = discord.Embed(
        title=f"📊 Niveau de {interaction.user.display_name}", 
        color=0x00ff00
    )
    embed.add_field(name="🏆 Niveau", value=f"**{level}**", inline=True)
    embed.add_field(name="⚡ XP actuelle", value=f"**{exp}**", inline=True)
    embed.add_field(name="🎯 XP manquante", value=f"**{exp_needed_next}**", inline=True)
    embed.add_field(name="📈 Messages envoyés", value=f"**{total_messages}**", inline=True)
    embed.add_field(name="🎭 Rang d'ancienneté", value=f"**{seniority_role}**", inline=True)
    embed.add_field(name="💎 XP pour ce niveau", value=f"**{exp_for_current}**", inline=True)

    # Barre de progression
    progress_percentage = (exp / calc_level_exp(level + 1)) * 100
    progress_bar = "█" * int(progress_percentage // 10) + "░" * (10 - int(progress_percentage // 10))
    embed.add_field(name="📊 Progression", value=f"`{progress_bar}` {progress_percentage:.1f}%", inline=False)

    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

@bot.tree.command(name="classement", description="Affiche le classement des membres du serveur")
async def leaderboard(interaction: discord.Interaction):
    """Affiche le classement des utilisateurs"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT username, level, exp, total_messages 
                     FROM user_levels 
                     ORDER BY level DESC, exp DESC 
                     LIMIT 15""")
    users = cursor.fetchall()

    if not users:
        await interaction.response.send_message("❌ Aucun utilisateur trouvé dans le classement!", ephemeral=True)
        conn.close()
        return

    embed = discord.Embed(
        title="🏆 Classement des Membres", 
        description="Top 15 des membres les plus actifs",
        color=0xffd700
    )

    medals = ["🥇", "🥈", "🥉"]

    for i, (username, level, exp, messages) in enumerate(users, 1):
        medal = medals[i-1] if i <= 3 else f"**{i}.**"
        seniority = get_seniority_role(level)

        embed.add_field(
            name=f"{medal} {username}",
            value=f"🏆 Niveau **{level}** • ⚡ **{exp}** XP\n📨 **{messages}** messages • 🎭 **{seniority}**",
            inline=False
        )

    embed.set_footer(text=f"Classement mis à jour • {len(users)} membres actifs")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)
    conn.close()

# === SYSTÈME DE PERSONNAGES ===

# Spécialités disponibles
SPECIALTIES = [
    "Chanteur", "Danseur", "Acteur", "Reporter", "Coach", "Mannequin",
    "Etudiant", "Professeur", "Influenceur", "Autre"
]

# Types de professeurs
PROFESSOR_TYPES = [
    "Professeur de chant", "Professeur de danse", "Professeur de théâtre",
    "Professeur de journalisme", "Educateur physique", "Professeur d'art"
]

@bot.tree.command(name="creer_personnage", description="Créer un nouveau personnage de jeu de rôle")
@app_commands.describe(nom="Le nom complet du personnage")
async def create_character(interaction: discord.Interaction, nom: str):
    """Créer un nouveau personnage"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Vérifier le nombre de personnages existants
    cursor.execute("SELECT COUNT(*) FROM characters WHERE user_id = ?", (interaction.user.id,))
    character_count = cursor.fetchone()[0]

    # Vérifier le niveau d'ancienneté de l'utilisateur
    cursor.execute("SELECT level FROM user_levels WHERE user_id = ?", (interaction.user.id,))
    user_data = cursor.fetchone()

    if not user_data:
        await interaction.response.send_message("❌ Vous devez d'abord envoyer des messages pour obtenir un niveau!", ephemeral=True)
        conn.close()
        return

    user_level = user_data[0]
    seniority_role = get_seniority_role(user_level)
    character_limit = get_character_limit(seniority_role)

    if character_count >= character_limit:
        await interaction.response.send_message(
            f"❌ Vous avez atteint la limite de **{character_limit}** personnages pour votre rang d'ancienneté (**{seniority_role}**)!\n"
            f"💡 Montez de niveau pour débloquer plus de personnages!",
            ephemeral=True
        )
        conn.close()
        return

    # Vérifier si le nom est déjà pris
    cursor.execute("SELECT * FROM characters WHERE character_name = ?", (nom,))
    if cursor.fetchone():
        await interaction.response.send_message("❌ Ce nom de personnage est déjà pris!", ephemeral=True)
        conn.close()
        return

    # Classes pour l'interface utilisateur
    class SpecialtySelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label=spec, 
                    value=spec,
                    description=get_specialty_description(spec)
                ) for spec in SPECIALTIES
            ]
            super().__init__(placeholder="Choisissez une spécialité...", options=options)

        async def callback(self, select_interaction: discord.Interaction):
            specialty = self.values[0]

            if specialty == "Autre":
                modal = CustomSpecialtyModal(nom)
                await select_interaction.response.send_modal(modal)
            elif specialty == "Professeur":
                # Afficher un deuxième menu pour le type de professeur
                view = ProfessorTypeView(nom)
                await select_interaction.response.edit_message(
                    content="Choisissez votre type de professeur:",
                    view=view
                )
            else:
                await create_character_with_specialty(select_interaction, nom, specialty)

    class ProfessorTypeSelect(discord.ui.Select):
        def __init__(self, char_name):
            self.char_name = char_name
            options = [
                discord.SelectOption(label=prof_type, value=prof_type) 
                for prof_type in PROFESSOR_TYPES
            ]
            super().__init__(placeholder="Choisissez votre spécialisation...", options=options)

        async def callback(self, select_interaction: discord.Interaction):
            specialty = self.values[0]
            await create_character_with_specialty(select_interaction, self.char_name, specialty)

    class ProfessorTypeView(discord.ui.View):
        def __init__(self, char_name):
            super().__init__(timeout=300)
            self.add_item(ProfessorTypeSelect(char_name))

    class CustomSpecialtyModal(discord.ui.Modal):
        def __init__(self, character_name):
            super().__init__(title="Spécialité personnalisée")
            self.character_name = character_name
            self.specialty_input = discord.ui.TextInput(
                label="Votre spécialité",
                placeholder="Ex: Photographe, Écrivain, Cuisinier...",
                max_length=50,
                min_length=2
            )
            self.add_item(self.specialty_input)

        async def on_submit(self, modal_interaction: discord.Interaction):
            specialty = self.specialty_input.value
            await create_character_with_specialty(modal_interaction, self.character_name, specialty)

    async def create_character_with_specialty(inter: discord.Interaction, char_name: str, specialty: str):
        """Créer le personnage avec la spécialité choisie"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()

        # Statistiques de base
        stats = {
            'chant': 1, 'danse': 1, 'eloquence': 1, 'acting': 1,
            'fitness': 1, 'esthetique': 1, 'reputation': 500
        }

        specialty_bonus = ""

        # Appliquer les bonus de spécialité
        if specialty == "Chanteur":
            stats['chant'] = 3
            specialty_bonus = "🎵 Chant niveau 3"
        elif specialty == "Danseur":
            stats['danse'] = 3
            specialty_bonus = "💃 Danse niveau 3"
        elif specialty == "Acteur":
            stats['acting'] = 3
            specialty_bonus = "🎭 Acting niveau 3"
        elif specialty == "Reporter":
            stats['eloquence'] = 3
            specialty_bonus = "🗣️ Éloquence niveau 3"
        elif specialty == "Coach":
            stats['fitness'] = 3
            specialty_bonus = "💪 Fitness niveau 3"
        elif specialty == "Mannequin":
            stats['esthetique'] = 3
            specialty_bonus = "✨ Esthétique niveau 3"
        elif specialty == "Influenceur":
            stats['reputation'] = 1000
            specialty_bonus = "⭐ Réputation 1000"
        elif "Professeur de chant" in specialty:
            stats['chant'] = 2
            specialty_bonus = "🎵 Chant niveau 2 + bonus XP 5%"
        elif "Professeur de danse" in specialty:
            stats['danse'] = 2
            specialty_bonus = "💃 Danse niveau 2 + bonus XP 5%"
        elif "Professeur de théâtre" in specialty:
            stats['acting'] = 2
            specialty_bonus = "🎭 Acting niveau 2 + bonus XP 5%"
        elif "Professeur de journalisme" in specialty:
            stats['eloquence'] = 2
            specialty_bonus = "🗣️ Éloquence niveau 2 + bonus XP 5%"
        elif "Educateur physique" in specialty:
            stats['fitness'] = 2
            specialty_bonus = "💪 Fitness niveau 2 + bonus XP 5%"
        elif "Professeur d'art" in specialty:
            stats['esthetique'] = 2
            specialty_bonus = "✨ Esthétique niveau 2 + bonus XP 5%"
        elif specialty == "Etudiant":
            specialty_bonus = "📚 Bonus XP entraînement +10%"

        # Créer le personnage
        cursor.execute("""INSERT INTO characters 
                         (user_id, character_name, specialty, chant, danse, eloquence, acting, fitness, esthetique, reputation)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (inter.user.id, char_name, specialty, stats['chant'], stats['danse'],
                       stats['eloquence'], stats['acting'], stats['fitness'], stats['esthetique'], stats['reputation']))

        conn.commit()
        conn.close()

        embed = discord.Embed(title="✨ Nouveau personnage créé!", color=0x00ff00)
        embed.add_field(name="📛 Nom", value=char_name, inline=True)
        embed.add_field(name="🎯 Spécialité", value=specialty, inline=True)
        embed.add_field(name="🎁 Bonus", value=specialty_bonus or "Aucun bonus", inline=False)

        stats_text = f"""
🎵 **Chant:** {stats['chant']}
💃 **Danse:** {stats['danse']}
🗣️ **Éloquence:** {stats['eloquence']}
🎭 **Acting:** {stats['acting']}
💪 **Fitness:** {stats['fitness']}
✨ **Esthétique:** {stats['esthetique']}
⭐ **Réputation:** {stats['reputation']}
        """
        embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)

        embed.set_footer(text=f"Créé par {inter.user.display_name}")
        embed.timestamp = datetime.now()

        await inter.response.edit_message(content=None, embed=embed, view=None)

    def get_specialty_description(specialty):
        """Retourne une description pour chaque spécialité"""
        descriptions = {
            "Chanteur": "Chant niveau 3",
            "Danseur": "Danse niveau 3", 
            "Acteur": "Acting niveau 3",
            "Reporter": "Éloquence niveau 3",
            "Coach": "Fitness niveau 3",
            "Mannequin": "Esthétique niveau 3",
            "Etudiant": "+10% XP entraînement",
            "Professeur": "Voir sous-spécialités",
            "Influenceur": "Réputation 1000",
            "Autre": "Spécialité personnalisée"
        }
        return descriptions.get(specialty, "")

    view = discord.ui.View(timeout=300)
    view.add_item(SpecialtySelect())

    embed = discord.Embed(
        title="🎭 Création de personnage",
        description=f"**Nom du personnage:** {nom}\n\nChoisissez la spécialité de votre personnage:",
        color=0x0099ff
    )
    embed.add_field(
        name="ℹ️ Informations",
        value=f"• Vous avez **{character_count}/{character_limit}** personnages\n• Rang d'ancienneté: **{seniority_role}**",
        inline=False
    )

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    conn.close()

@bot.tree.command(name="mes_personnages", description="Voir la liste de vos personnages")
async def list_characters(interaction: discord.Interaction):
    """Affiche la liste des personnages de l'utilisateur"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT character_name, specialty, chant, danse, eloquence, acting, fitness, esthetique, reputation
                     FROM characters WHERE user_id = ? ORDER BY created_at""", (interaction.user.id,))
    characters = cursor.fetchall()

    if not characters:
        await interaction.response.send_message("❌ Vous n'avez aucun personnage créé!", ephemeral=True)
        conn.close()
        return

    embed = discord.Embed(
        title=f"🎭 Personnages de {interaction.user.display_name}",
        color=0x9932cc
    )

    for char_name, specialty, chant, danse, eloquence, acting, fitness, esthetique, reputation in characters:
        total_level = chant + danse + eloquence + acting + fitness + esthetique
        embed.add_field(
            name=f"📛 {char_name}",
            value=f"🎯 **{specialty}**\n📊 Niveau total: **{total_level}**\n⭐ Réputation: **{reputation}**",
            inline=True
        )

    embed.set_footer(text=f"Total: {len(characters)} personnage(s)")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

@bot.tree.command(name="stats_personnage", description="Voir les statistiques détaillées d'un personnage")
@app_commands.describe(nom="Le nom du personnage")
async def character_stats(interaction: discord.Interaction, nom: str):
    """Affiche les statistiques d'un personnage"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM characters WHERE character_name = ? AND user_id = ?", (nom, interaction.user.id))
    character = cursor.fetchone()

    if not character:
        await interaction.response.send_message("❌ Personnage non trouvé ou ne vous appartient pas!", ephemeral=True)
        conn.close()
        return

    embed = discord.Embed(
        title=f"📊 Statistiques de {character[2]}", 
        description=f"🎯 **Spécialité:** {character[3]}",
        color=0x0099ff
    )

    # Statistiques avec barres de progression
    stats = [
        ("🎵 Chant", character[4], character[11]),
        ("💃 Danse", character[5], character[12]),
        ("🗣️ Éloquence", character[6], character[13]),
        ("🎭 Acting", character[7], character[14]),
        ("💪 Fitness", character[8], character[15]),
        ("✨ Esthétique", character[9], character[16])
    ]

    for stat_name, level, exp in stats:
        exp_needed = calc_stat_exp(level + 1)
        progress = (exp / exp_needed) * 100 if exp_needed > 0 else 0
        progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))

        embed.add_field(
            name=stat_name,
            value=f"**Niveau {level}** ({exp}/{exp_needed} XP)\n`{progress_bar}` {progress:.1f}%",
            inline=True
        )

    embed.add_field(
        name="⭐ Réputation",
        value=f"**{character[10]}** points",
        inline=True
    )

    total_level = sum(character[4:10]) - character[10]  # Exclure la réputation du total
    embed.add_field(
        name="📈 Niveau total",
        value=f"**{total_level}** niveaux",
        inline=True
    )

    embed.set_footer(text=f"Personnage de {interaction.user.display_name}")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

@bot.tree.command(name="entrainer", description="Entraîner une statistique de votre personnage")
@app_commands.describe(
    nom="Le nom du personnage",
    statistique="La statistique à entraîner"
)
@app_commands.choices(statistique=[
    app_commands.Choice(name="🎵 Chant", value="chant"),
    app_commands.Choice(name="💃 Danse", value="danse"),
    app_commands.Choice(name="🗣️ Éloquence", value="eloquence"),
    app_commands.Choice(name="🎭 Acting", value="acting"),
    app_commands.Choice(name="💪 Fitness", value="fitness"),
    app_commands.Choice(name="✨ Esthétique", value="esthetique")
])
async def train_character(interaction: discord.Interaction, nom: str, statistique: str):
    """Entraîner une statistique d'un personnage"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM characters WHERE character_name = ? AND user_id = ?", (nom, interaction.user.id))
    character = cursor.fetchone()

    if not character:
        await interaction.response.send_message("❌ Personnage non trouvé ou ne vous appartient pas!", ephemeral=True)
        conn.close()
        return

    # Calculer l'XP gagnée
    base_exp = random.randint(750, 1250)
    multiplier = 1.0
    specialty = character[3]

    # Bonus pour les étudiants
    if specialty == "Etudiant":
        multiplier *= 1.1  # +10%

    # Bonus pour les professeurs spécialisés
    elif "Professeur" in specialty:
        stat_matches = {
            "chant": "chant",
            "danse": "danse", 
            "acting": "théâtre",
            "eloquence": "journalisme",
            "fitness": "physique",
            "esthetique": "art"
        }

        if stat_matches.get(statistique, "").lower() in specialty.lower():
            multiplier *= 1.05  # +5%

    final_exp = int(base_exp * multiplier)

    # Récupérer les statistiques actuelles
    stat_indices = {
        'chant': (4, 11), 'danse': (5, 12), 'eloquence': (6, 13),
        'acting': (7, 14), 'fitness': (8, 15), 'esthetique': (9, 16)
    }

    level_idx, exp_idx = stat_indices[statistique]
    current_level = character[level_idx]
    current_exp = character[exp_idx]

    new_exp = current_exp + final_exp
    new_level = current_level
    levels_gained = 0

    # Vérifier les montées de niveau
    while True:
        exp_needed = calc_stat_exp(new_level + 1)
        if new_exp >= exp_needed:
            new_level += 1
            new_exp -= exp_needed
            levels_gained += 1
        else:
            break

    # Mettre à jour la base de données
    cursor.execute(f"UPDATE characters SET {statistique} = ?, {statistique}_exp = ? WHERE id = ?",
                   (new_level, new_exp, character[0]))

    conn.commit()
    conn.close()

    # Créer la réponse
    stat_names = {
        'chant': '🎵 Chant',
        'danse': '💃 Danse',
        'eloquence': '🗣️ Éloquence',
        'acting': '🎭 Acting',
        'fitness': '💪 Fitness',
        'esthetique': '✨ Esthétique'
    }

    embed = discord.Embed(title="🏋️ Entraînement terminé!", color=0x00ff00)
    embed.add_field(name="📛 Personnage", value=nom, inline=True)
    embed.add_field(name="📊 Statistique", value=stat_names[statistique], inline=True)
    embed.add_field(name="⚡ XP gagnée", value=f"**{final_exp}** XP", inline=True)

    if multiplier > 1.0:
        bonus_percent = (multiplier - 1.0) * 100
        embed.add_field(name="🎁 Bonus", value=f"+{bonus_percent:.0f}% ({specialty})", inline=True)

    if levels_gained > 0:
        if levels_gained == 1:
            embed.add_field(name="🎉 Niveau atteint!", value=f"Niveau **{new_level}**", inline=False)
        else:
            embed.add_field(name="🚀 Niveaux gagnés!", value=f"**{levels_gained}** niveaux! Nouveau niveau: **{new_level}**", inline=False)
        embed.color = 0xffd700

    embed.set_footer(text=f"Entraînement par {interaction.user.display_name}")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="supprimer_personnage", description="Supprimer un de vos personnages")
@app_commands.describe(nom="Le nom du personnage à supprimer")
async def delete_character(interaction: discord.Interaction, nom: str):
    """Supprimer un personnage avec confirmation"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM characters WHERE character_name = ? AND user_id = ?", (nom, interaction.user.id))
    character = cursor.fetchone()

    if not character:
        await interaction.response.send_message("❌ Personnage non trouvé ou ne vous appartient pas!", ephemeral=True)
        conn.close()
        return

    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
        async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM characters WHERE id = ?", (character[0],))
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🗑️ Personnage supprimé",
                description=f"Le personnage **{nom}** a été définitivement supprimé.",
                color=0xff0000
            )
            embed.set_footer(text=f"Suppression confirmée par {button_interaction.user.display_name}")

            await button_interaction.response.edit_message(content=None, embed=embed, view=None)

        @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
        async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(
                title="❌ Suppression annulée",
                description=f"Le personnage **{nom}** n'a pas été supprimé.",
                color=0x808080
            )
            await button_interaction.response.edit_message(content=None, embed=embed, view=None)

    view = ConfirmView()

    embed = discord.Embed(
        title="⚠️ Confirmation de suppression",
        description=f"Êtes-vous **vraiment sûr** de vouloir supprimer le personnage **{nom}** ?\n\n⚠️ **Cette action est irréversible!**",
        color=0xffa500
    )
    embed.add_field(
        name="📊 Statistiques du personnage",
        value=f"🎯 Spécialité: {character[3]}\n📈 Niveaux cumulés: {sum(character[4:10]) - character[10]}",
        inline=False
    )

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    conn.close()

# === COMMANDES D'ADMINISTRATION (OPTIONNELLES) ===

@bot.tree.command(name="admin_reset_user", description="[ADMIN] Remettre à zéro le niveau d'un utilisateur")
@app_commands.describe(utilisateur="L'utilisateur à remettre à zéro")
async def admin_reset_user(interaction: discord.Interaction, utilisateur: discord.Member):
    """Commande d'administration pour remettre à zéro un utilisateur"""
    # Vérifier si l'utilisateur a les permissions d'administrateur
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Vous n'avez pas les permissions pour utiliser cette commande!", ephemeral=True)
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Supprimer l'utilisateur de la base de données
    cursor.execute("DELETE FROM user_levels WHERE user_id = ?", (utilisateur.id,))
    cursor.execute("DELETE FROM characters WHERE user_id = ?", (utilisateur.id,))

    conn.commit()
    conn.close()

    # Supprimer tous les rôles d'ancienneté
    old_roles = ["newcomer", "rising", "yapper", "go outside touch some grass"]
    for role_name in old_roles:
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role and role in utilisateur.roles:
            try:
                await utilisateur.remove_roles(role)
            except discord.Forbidden:
                pass

    embed = discord.Embed(
        title="🔄 Utilisateur remis à zéro",
        description=f"L'utilisateur {utilisateur.mention} a été remis à zéro.\n\n✅ Niveau et XP supprimés\n✅ Personnages supprimés\n✅ Rôles d'ancienneté retirés",
        color=0x00ff00
    )

    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    # Vérification du token
    if TOKEN == "VOTRE_TOKEN_ICI":
        print("❌ ERREUR: Vous devez remplacer TOKEN par votre vrai token Discord!")
        print("📝 Instructions:")
        print("1. Allez sur https://discord.com/developers/applications")
        print("2. Créez une nouvelle application")
        print("3. Allez dans l'onglet 'Bot'")
        print("4. Copiez le token et remplacez 'VOTRE_TOKEN_ICI' dans le code")
    else:
        print("🚀 Démarrage du bot...")
        bot.run(TOKEN)
