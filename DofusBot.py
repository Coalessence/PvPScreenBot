import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import json
from extractScreen import DofusScreenExtractor
import asyncio

load_dotenv()
TOKEN=os.getenv("DISCORDTOKEN")
serverList=json.loads(os.getenv("SERVERS"))

path_to_tesseract = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
conf= "--psm 6 -l eng+ita+fra+rus"

dse=DofusScreenExtractor(path_to_tesseract, conf)


class DofusBot(discord.Client):
    def __init__(self, guildList):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.guildList=guildList
    
    async def on_ready(self):
        await self.wait_until_ready()
        print(f'logged on as {self.user}! in {self.guilds[0].name}')
    
    async def setup_hook(self):
        for guildItem in self.guildList:
            self.tree.copy_global_to(guild=discord.Object(id=guildItem))
            await self.tree.sync(guild=discord.Object(id=guildItem))
    
    def run(self):
        super().run(TOKEN)

client=DofusBot(serverList)
        
@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""#
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')
    
@client.tree.command()
async def upload(interaction: discord.Interaction, attachment: discord.Attachment):

    await interaction.response.defer()
    res=await dse.extractMain(attachment.url)
    
    
    print(res)
    await interaction.followup.send(f'{res}')
