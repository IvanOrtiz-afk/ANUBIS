from flask import Flask
from threading import Thread
import discord
import asyncio
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os
import unicodedata
from discord import app_commands

# --- Flask para keep alive ---
app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# --- CONFIGURACIÓN ---
with open("token.txt") as f:
    TOKEN = f.read().strip()

ID_CANAL_REGISTRO = 1464446801993142314
LOG_CHANNEL_ID = 1464448974445613056
ROL_REGISTRO_ID = 1464445072580804658
CANAL_IMAGENES_ID = 1464447745115947217
NICK_PREFIJO = "-RO-"

# Jerarquía de roles
ROL_JERARQUIA = [
    1464776049677041767,
    1464445738531553416,
    1464445499955351633,
    1464445072580804658,
    1464444635278475348,
    1464443931172536330,
    1464443110095454218,
    1481072446307172372,
    1464442595370336559,
    1464442255602614302,
    1464441965876744283,
    1464439157270253672,
]

# --- ROLES PARA /PING ---
ROLES_PING = {
    "invitado": 1464776049677041767,
    "cryosueno": 1464445738531553416,
    "tennoentrante": 1464445499955351633,
    "recienllegado": 1464445072580804658,
    "tennointegrante": 1464444635278475348,
    "ciudadanotau": 1464443931172536330,
    "feudalnarmer": 1464443110095454218,
    "granarquimediano": 1481072446307172372,
    "reclutador": 1464442595370336559,
    "maestro": 1464442255602614302,
    "colider": 1464441965876744283,
    "liderfundador": 1464439157270253672
}

# --- ROLES QUE NO GENERAN IMAGEN ---
ROLES_SIN_IMAGEN = {
    1464776049677041767,
    1464445738531553416,
    1464445499955351633,
    1464445072580804658
}

# --- INTENTS ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- FUNCIONES DE IMÁGENES ---
def cargar_fondo(tipo):
    ruta = f"fondo/{tipo}.png"
    if os.path.exists(ruta):
        return ruta
    return None

def normalizar_texto(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFKC', texto)
        if unicodedata.category(c)[0] != 'M'
    )

def dibujar_texto_con_borde(draw, pos, texto, font, fill, borde=2):
    x, y = pos
    for dx in range(-borde, borde+1):
        for dy in range(-borde, borde+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y+dy), texto, font=font, fill=(0,0,0))
    draw.text(pos, texto, font=font, fill=fill)

async def crear_imagen(member, texto, tipo="bienvenida"):

    fondo_path = cargar_fondo(tipo)
    if fondo_path:
        fondo = Image.open(fondo_path).convert("RGBA")
    else:
        fondo = Image.new("RGBA", (900,450), (25,25,35))

    ancho_fondo, alto_fondo = fondo.size

    url = member.display_avatar.url
    response = requests.get(url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
    avatar_size = 220
    avatar = avatar.resize((avatar_size, avatar_size))

    mask = Image.new("L", avatar.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0,0,avatar_size,avatar_size), fill=255)

    marco_size = avatar_size + 12
    marco = Image.new("RGBA", (marco_size, marco_size), (255,255,255,0))
    draw_marco = ImageDraw.Draw(marco)
    draw_marco.ellipse((0,0,marco_size,marco_size), fill=(255,255,255,255))
    marco.paste(avatar, (6,6), mask)

    pos_avatar_x = (ancho_fondo - marco_size)//2
    pos_avatar_y = 50
    fondo.paste(marco, (pos_avatar_x, pos_avatar_y), marco)

    draw = ImageDraw.Draw(fondo)

    fuente_nombre = ImageFont.truetype("fuentes/NewRocker-Regular.ttf", 70)
    fuente_sec = ImageFont.truetype("fuentes/NewRocker-Regular.ttf", 50)

    nombre_text = str(member.name)

    w, h = draw.textbbox((0,0), nombre_text, font=fuente_nombre)[2:]
    while w > ancho_fondo - 60:
        size = fuente_nombre.size - 2
        if size < 40: break
        fuente_nombre = ImageFont.truetype("fuentes/NewRocker-Regular.ttf", size)
        w, h = draw.textbbox((0,0), nombre_text, font=fuente_nombre)[2:]

    pos_nombre_x = (ancho_fondo - w)//2
    pos_nombre_y = pos_avatar_y + marco_size + 10

    dibujar_texto_con_borde(draw,(pos_nombre_x,pos_nombre_y),nombre_text,fuente_nombre,(255,255,255))

    if tipo == "bienvenida":
        texto_sec = f"{texto} {normalizar_texto(member.guild.name)}"
    else:
        texto_sec = normalizar_texto(texto)

    w_sec, h_sec = draw.textbbox((0,0), texto_sec, font=fuente_sec)[2:]

    pos_sec_x = (ancho_fondo - w_sec)//2
    pos_sec_y = pos_nombre_y + h + 10

    dibujar_texto_con_borde(draw,(pos_sec_x,pos_sec_y),texto_sec,fuente_sec,(255,255,255))

    buffer = BytesIO()
    fondo.save(buffer,"PNG")
    buffer.seek(0)

    return discord.File(buffer, filename="imagen.png")


# --- BOT LISTO ---
@client.event
async def on_ready():

    await tree.sync()

    print("======================================")
    print(f"Bot iniciado como: {client.user}")
    print("Slash commands sincronizados")
    print("======================================")


# --- SLASH COMMAND /PING ---
@tree.command(name="ping", description="Menciona un rol del servidor")
async def ping(interaction: discord.Interaction, rol: str, mensaje: str = ""):

    rol = rol.lower().replace(" ", "")

    if rol in ROLES_PING:

        role_id = ROLES_PING[rol]

        await interaction.response.send_message(
            f"<@&{role_id}> {mensaje}"
        )

    else:

        await interaction.response.send_message(
            "Ese rol no existe.",
            ephemeral=True
        )


# --- BIENVENIDA ---
@client.event
async def on_member_join(member):

    canal = client.get_channel(CANAL_IMAGENES_ID)

    if canal:
        img = await crear_imagen(member,"Bienvenido a ",tipo="bienvenida")
        await canal.send(file=img)


# --- DESPEDIDA ---
@client.event
async def on_member_remove(member):

    canal = client.get_channel(CANAL_IMAGENES_ID)

    if canal:
        img = await crear_imagen(member,"Se nos fue...",tipo="despedida")
        await canal.send(file=img)


# --- REGISTRO ---
@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != ID_CANAL_REGISTRO:
        return

    member = message.author

    if not member.guild_permissions.administrator:

        if member.display_name.startswith(NICK_PREFIJO):

            aviso = await message.channel.send("⚠️ Ya estás registrado.")
            await asyncio.sleep(5)

            try:
                await aviso.delete()
                await message.delete()
            except:
                pass

            return

    nombre = message.content.strip()

    nuevo_nick = f"{NICK_PREFIJO}{nombre}"

    if len(nuevo_nick) > 32:

        msg = await message.channel.send(
            f"⚠️ {member.mention}, el nombre es demasiado largo."
        )

        await asyncio.sleep(5)

        try:
            await msg.delete()
            await message.delete()
        except:
            pass

        return

    try:

        await member.edit(nick=nuevo_nick)

        rol_registro = message.guild.get_role(ROL_REGISTRO_ID)

        if rol_registro not in member.roles:
            await member.add_roles(rol_registro)

        confirm = await message.channel.send(
            f"✅ Registro completado: **{nuevo_nick}**"
        )

        log = client.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(
                f"📋 Nuevo registro\nUsuario: {member.mention}\nNick: {nuevo_nick}"
            )

        await asyncio.sleep(5)

        try:
            await confirm.delete()
            await message.delete()
        except:
            pass

    except discord.Forbidden:

        error = await message.channel.send(
            f"❌ No puedo cambiar tu nombre {member.mention}.\nRevisa los permisos del bot."
        )

        await asyncio.sleep(7)

        try:
            await error.delete()
            await message.delete()
        except:
            pass


# --- ROLES NUEVOS + BLOQUEO NICK ---
@client.event
async def on_member_update(before, after):

    roles_antes = set(before.roles)
    roles_despues = set(after.roles)

    nuevos_roles = roles_despues - roles_antes

    if nuevos_roles:

        canal = client.get_channel(CANAL_IMAGENES_ID)

        max_rol_antes = max(
            (ROL_JERARQUIA.index(r.id) for r in before.roles if r.id in ROL_JERARQUIA),
            default=-1
        )

        for rol in nuevos_roles:

            if rol.id in ROLES_SIN_IMAGEN:
                continue

            if rol.id in ROL_JERARQUIA:

                idx_rol = ROL_JERARQUIA.index(rol.id)

                if idx_rol > max_rol_antes:

                    if canal:

                        rol_texto = normalizar_texto(f"Recibió el rol: {rol.name}")

                        img = await crear_imagen(after, rol_texto, tipo="rol")

                        await canal.send(file=img)

    if before.nick == after.nick:
        return

    if after.guild_permissions.administrator:
        return

    try:

        if before.nick and before.nick.startswith(NICK_PREFIJO):
            if not after.nick or not after.nick.startswith(NICK_PREFIJO):
                await after.edit(nick=before.nick)

    except:
        pass


# --- INICIO ---
if __name__ == "__main__":

    try:

        keep_alive()

        client.run(TOKEN)

    except Exception as e:

        print(e)