# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from datetime import datetime

from telethon import TelegramClient,events 
from telethon import __version__ as telever
from pyrogram import __version__ as pyrover
from telethon.tl.types import KeyboardButtonCallback
from ..core.getCommand import get_command
from ..core.getVars import get_val
from ..utils.speedtest import get_speed
from ..utils import human_format
from ..utils.misc_utils import clear_stuff
from ..utils.admin_check import is_admin
from .. import uptime
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from .settings import handle_settings, handle_setting_callback
from bot.downloaders.telegram_download import down_load_media_pyro
import asyncio as aio
import re,logging,time,os,psutil,shutil, signal
from bot import __version__
torlog = logging.getLogger(__name__)

def add_handlers(bot: TelegramClient):
      
    #pyro handler
    download_handler = MessageHandler(
        handle_download_command,
        filters= filters.command(["leech"],
    ))
    bot.pyro.add_handler(download_handler)
    
    #telethon handlers

    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command("EXEC")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        about_me,
        events.NewMessage(pattern=command_process(get_command("ABOUT")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        get_logs_f,
        events.NewMessage(pattern=command_process(get_command("GETLOGS")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_test_command,
        events.NewMessage(pattern="/test",
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_server_command,
        events.NewMessage(pattern=command_process(get_command("SERVER")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        start_handler,
        events.NewMessage(pattern=command_process(get_command("START")))
    )

    bot.add_event_handler(
        speed_handler,
        events.NewMessage(pattern=command_process(get_command("SPEEDTEST")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        cleardata_handler,
        events.NewMessage(pattern=command_process(get_command("CRLDATA")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_settings_command,
        events.NewMessage(pattern=command_process(get_command("SETTINGS")),
        chats=get_val("ALD_USR"))
    )

    #signal.signal(signal.SIGINT, partial(term_handler,client=bot))
    #signal.signal(signal.SIGTERM, partial(term_handler,client=bot))
    bot.loop.run_until_complete(booted(bot))

    #*********** Callback Handlers *********** 
    
    bot.add_event_handler(
        handle_cancel,
        events.CallbackQuery(pattern="upcancel")
    )

    bot.add_event_handler(
        handle_server_command,
        events.CallbackQuery(pattern="fullserver")
    )
    bot.add_event_handler(
        cleardata_handler,
        events.CallbackQuery(pattern="cleardata")
    )

    bot.add_event_handler(
        handle_settings_cb,
        events.CallbackQuery(pattern="setting")
    )
#*********** Handlers Below ***********

     
async def handle_download_command(client, message):
       await down_load_media_pyro(client, message)

async def speed_handler(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await get_speed(e)

    
async def handle_test_command(e):
    pass


async def handle_cancel_all(e):
    try:
        # iterating through each instance of the process
        for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
            fields = line.split()
             
            # extracting Process ID from the output
            pid = fields[0]
             
            # terminating process
            os.kill(int(pid), signal.SIGKILL)

            await e.answer("Upload has been canceled ", alert=True)
    except:
        print("Error Encountered while running script")
        
        
async def handle_cancel(e):
    try:
            data = e.data.decode("UTF-8")
            torlog.info("Data is {}".format(data))
            data = data.split(" ")
        
            pid = data[1]
             
            # terminating process
            os.kill(int(pid), signal.SIGKILL)

            await e.answer("Upload has been canceled ", alert=True)
    except:
        print("Error Encountered while running script")

async def callback_handler_canc(e):
  pass

async def handle_settings_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_settings(e)
    else:
        await e.delete()
 
async def handle_settings_cb(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_setting_callback(e)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.",alert=True)

async def handle_exec_message_f(e):
    if get_val("REST11"):
        return
    message = e
    client = e.client
    if await is_admin(client, message.sender_id, message.chat_id, force_owner=True):
        PROCESS_RUN_TIME = 100
        cmd = message.text.split(" ", maxsplit=1)[1]

        reply_to_id = message.id
        if message.is_reply:
            reply_to_id = message.reply_to_msg_id

        process = await aio.create_subprocess_shell(
            cmd,
            stdout=aio.subprocess.PIPE,
            stderr=aio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        e = stderr.decode()
        if not e:
            e = "No Error"
        o = stdout.decode()
        if not o:
            o = "No Output"
        else:
            _o = o.split("\n")
            o = "`\n".join(_o)
        OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"

        if len(OUTPUT) > 3900:
            with open("exec.text", "w+", encoding="utf8") as out_file:
                out_file.write(str(OUTPUT))
            await client.send_file(
                entity=message.chat_id,
                file="exec.text",
                caption=cmd,
                reply_to=reply_to_id
            )
            os.remove("exec.text")
            await message.delete()
        else:
            await message.reply(OUTPUT)
    else:
        await message.reply("Only for owner")


async def get_logs_f(e):
    if await is_admin(e.client,e.sender_id,e.chat_id, force_owner=True):
        await e.client.send_file(
            entity=e.chat_id,
            file="torlog.txt",
            caption="torlog.txt",
            reply_to=e.message.id
        )
    else:
        await e.delete()

async def start_handler(event):
    msg = "Hello Welcome. Enjoy this bot."
    await event.reply(msg)

def progress_bar(percentage):
    """Returns a progress bar for download
    """
    #percentage is on the scale of 0-1
    comp = get_val("COMPLETED_STR")
    ncomp = get_val("REMAINING_STR")
    pr = ""

    if isinstance(percentage, str):
        return "NaN"

    try:
        percentage=int(percentage)
    except:
        percentage = 0

    for i in range(1,11):
        if i <= int(percentage/10):
            pr += comp
        else:
            pr += ncomp
    return pr    

async def handle_server_command(message):
    print(type(message))
    if isinstance(message, events.CallbackQuery.Event):
        callbk = True
    else:
        callbk = False

    try:
        # Memory
        mem = psutil.virtual_memory()
        memavailable = human_format.human_readable_bytes(mem.available)
        memtotal = human_format.human_readable_bytes(mem.total)
        mempercent = mem.percent
        memfree = human_format.human_readable_bytes(mem.free)
    except:
        memavailable = "N/A"
        memtotal = "N/A"
        mempercent = "N/A"
        memfree = "N/A"

    try:
        # Frequencies
        cpufreq = psutil.cpu_freq()
        freqcurrent = cpufreq.current
        freqmax = cpufreq.max
    except:
        freqcurrent = "N/A"
        freqmax = "N/A"

    try:
        # Cores
        cores = psutil.cpu_count(logical=False)
        lcores = psutil.cpu_count()
    except:
        cores = "N/A"
        lcores = "N/A"

    try:
        cpupercent = psutil.cpu_percent()
    except:
        cpupercent = "N/A"
    
    try:
        # Storage
        usage = shutil.disk_usage("/")
        totaldsk = human_format.human_readable_bytes(usage.total)
        useddsk = human_format.human_readable_bytes(usage.used)
        freedsk = human_format.human_readable_bytes(usage.free)
    except:
        totaldsk = "N/A"
        useddsk = "N/A"
        freedsk = "N/A"


    try:
        upb, dlb = 0,0
        dlb = human_format.human_readable_bytes(dlb)
        upb = human_format.human_readable_bytes(upb)
    except:
        dlb = "N/A"
        upb = "N/A"

    diff = time.time() - uptime
    diff = human_format.human_readable_timedelta(diff)

    if callbk:
        msg = (
            f"<b>BOT UPTIME:-</b> {diff}\n\n"
            "<b>CPU STATS:-</b>\n"
            f"Cores: {cores} Logical: {lcores}\n"
            f"CPU Frequency: {freqcurrent}  Mhz Max: {freqmax}\n"
            f"CPU Utilization: {cpupercent}%\n"
            "\n"
            "<b>STORAGE STATS:-</b>\n"
            f"Total: {totaldsk}\n"
            f"Used: {useddsk}\n"
            f"Free: {freedsk}\n"
            "\n"
            "<b>MEMORY STATS:-</b>\n"
            f"Available: {memavailable}\n"
            f"Total: {memtotal}\n"
            f"Usage: {mempercent}%\n"
            f"Free: {memfree}\n"
            "\n"
            "<b>TRANSFER INFO:</b>\n"
            f"Download: {dlb}\n"
            f"Upload: {upb}\n"
        )
        await message.edit(msg, parse_mode="html", buttons=None)
    else:
        try:
            storage_percent = round((usage.used/usage.total)*100,2)
        except:
            storage_percent = 0

        
        msg = (
            f"<b>BOT UPTIME:-</b> {diff}\n\n"
            f"CPU Utilization: {progress_bar(cpupercent)} - {cpupercent}%\n\n"
            f"Storage used:- {progress_bar(storage_percent)} - {storage_percent}%\n"
            f"Total: {totaldsk} Free: {freedsk}\n\n"
            f"Memory used:- {progress_bar(mempercent)} - {mempercent}%\n"
            f"Total: {memtotal} Free: {memfree}\n\n"
            f"Transfer Download:- {dlb}\n"
            f"Transfer Upload:- {upb}\n"
        )
        await message.reply(msg, parse_mode="html", buttons=[[KeyboardButtonCallback("Get detailed stats.","fullserver")]])


async def about_me(message):
    val1  = get_val("RCLONE_ENABLED")
    if val1 is not None:
        if val1:
            rclone = "Rclone enabled by admin."
        else:
            rclone = "Rclone disabled by admin."
    else:
        rclone = "N/A"

    val1  = get_val("LEECH_ENABLED")
    if val1 is not None:
        if val1:
            leen = "Leech command enabled by admin."
        else:
            leen = "Leech command disabled by admin."
    else:
        leen = "N/A"


    diff = time.time() - uptime
    diff = human_format.human_readable_timedelta(diff)

    msg = (
        "<b>Name</b>: <code>RcloneTg1.0</code>\n"
        f"<b>Telethon Version</b>: {telever}\n"
        f"<b>Pyrogram Version</b>: {pyrover}\n"
        "<u>Currents Configs:-</u>\n\n"
        f"<b>Bot Uptime:-</b> {diff}\n"
        "<b>Upload Engine:-</b> <code>RCLONE</code> \n"
        f"<b>Leech:- </b> <code>{leen}</code>\n"
        f"<b>Rclone:- </b> <code>{rclone}</code>\n"
        "\n"
    )

    await message.reply(msg,parse_mode="html")


async def cleardata_handler(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        if isinstance(e, events.CallbackQuery.Event):
            data = e.data.decode("UTF-8").split(" ")
            if data[1] == "yes":
                await e.answer("Clearing data.")
                await e.edit("Cleared Data @ {}".format(datetime.now().strftime("%d-%B-%Y, %H:%M:%S")))
                await clear_stuff("userdata")
                await clear_stuff("./DOWNLOADS")
                await clear_stuff("bot/DOWNLOADS")
                await clear_stuff("app/bot/DOWNLOADS")
                os.mkdir("userdata")
            else:
                await e.answer("Aborting.")
                await e.delete()
        else:
            buttons = [[KeyboardButtonCallback("Yes", data="cleardata yes"),KeyboardButtonCallback("No", data="cleardata no")]]
            await e.reply("Are you sure you want to clear data?\n"
                          "This will delete all your data, including your downloaded files and will affect any ongoing transfers.\n", buttons=buttons)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.",alert=True)


async def booted(client):
    chats = get_val("ALD_USR")
    for i in chats:
        try:
            await client.send_message(i, "The bot is booted and is ready to use.")
        except Exception as e:
            torlog.info(f"Not found the entity {i}")

def command_process(command):
    return re.compile(command,re.IGNORECASE)
