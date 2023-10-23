
"""
-------------  MADE BY : ُEng.Hassan Syaed --------------------

"""


#!/usr/bin/python

# Set Up An Enviroment
"""
   Installing Packages   
   =====================

   # Pytube for dealing with Youtube streams
   pip insatll git+https://githube.com/pytube/pytube

   # pytelegrambotapi for dealing with Telegram
   pip install pytelegrambotapi

"""
from dotenv import load_dotenv
from pytube import YouTube
import telebot
import requests
import os

"""---- YouTube Fucntions And Handlers ---"""

# Return To Me A Valid Obj

def Valid_Obj(URL):
    try:
       YT_OBJ = YouTube(URL)
       return YT_OBJ
    except:
       return False

# Download Only Audio
def Download_Audio(yt_vid_obj):

    audio = yt_vid_obj.streams.filter(only_audio=True).first()
    return audio.download()

# Returns All Available Qualites Of A Video That's Has An Audio (Video+Audio).
def Sizes_And_Qualities(yt_obj):

    qualities = []
    sizes = []

    try:
      stream = yt_obj.streams
      for res in stream.filter(progressive=True):
          quality = res.resolution
          size = stream.filter(progressive=True , res=quality).first().filesize /(1024*1024)

          # Only 500 MB Or Less Files Allowed(For Quota Considrations)
          # This Part Can Be Commented In Free Storage Case.
          if size <=500:
             qualities.append(quality)
             sizes.append(size)

      qualities_sizes = [qualities , sizes]
      return qualities_sizes

    except Exception as e:
      
      return ["ERROR", f"{e}"]
# Download The Video With The Given Available Quality
def Download_Video(yt_obj , selected_res):
    stream = yt_obj.streams.filter(progressive=True,res=selected_res).first()
    return stream.download()

# Error handling decorator
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            return "ERROR"
    return wrapper


""" ------------ Telegram Handling --------- """
"""
# Strongly Adviced To Store Your API Key In .env File And Use This Part Of Code To Configure It.

load_dotenv()
API= os.getenv('BOT_API_KEY')
"""

API = "PUT YOUR VALID API KEY OF TELEGRAM "
bot = telebot.TeleBot(API)

# Sending The Downloaded Video To The Telegram User
def Send_Video(File , chat_id):

   url = f'https://api.telegram.org/bot{API}/sendDocument' 
   files = {'document': open(File , "rb")}
   data = {'chat_id': chat_id}

   try:
      respond = requests.post(url , data=data , files=files)
      if respond.status_code  == 200:
         return "DONE"
      else:
         return "NOTDONE"
   except:
         return "ERROR"

@bot.message_handler(commands =["start"])
@error_handler
def URL_Message(message):
    chat_id = message.chat.id
    MSG = bot.send_message(chat_id , "Enter The URL Of The Youtube Video : ")
    bot.register_next_step_handler(MSG , Video_Audio_Choice)


def Video_Audio_Choice(message):
    chat_id =message.chat.id

    YT_OBJ = Valid_Obj(message.text)

    # In-Valid Video URL Given 
    if YT_OBJ ==False:
       bot.reply_to(message ,"Invalid URL.Please Check URL Validity And Try Again./start")

    else:
       bot.send_message(chat_id , "Your Video Being Handled , Please Be Patient :) ")
       global YOUTUBE_OBJ

       YOUTUBE_OBJ = YT_OBJ

       # Video Restrictions Or Errors Found. 
       if Sizes_And_Qualities(YT_OBJ)[0] == "ERROR":

          bot.reply_to(message ,f"ERROR !.{Sizes_And_Qualities(YT_OBJ)[1]}Press /start And Try Another Video")

       else:
          # Making Video & Audio Choice 
          markup = telebot.types.InlineKeyboardMarkup()
          video_btn = telebot.types.InlineKeyboardButton("video" , callback_data = "video")
          audio_btn = telebot.types.InlineKeyboardButton("audio" , callback_data = "audio")
          markup.add(video_btn , audio_btn)

          try:
             bot.send_message(chat_id , "Choose The Downloading Format Of Your Video." , reply_markup = markup)
          except :
             bot.send_message(chat_id , "An Error Happend While Choosing, Please Make Sure You Are Choosing Only One Choice.")

@bot.callback_query_handler(func=lambda call : True)
@error_handler
def res(call):

    if call.data == "video":

       global VIDS

       VIDS = Sizes_And_Qualities(YOUTUBE_OBJ)

       quality_markup = telebot.types.InlineKeyboardMarkup()

       # Btn_Name , callback_data
       buttons = [("144p","144p") , ("240p","240p") , ("360p","360p") , ("480p","480p") , ("720p","720p") , ("1080p","1080p")]

       for btn_name , call_back in buttons:

          if btn_name in VIDS[0]:
            size_formatted= f"{VIDS[1][VIDS[0].index(btn_name)]:.2f}"
            quality_btn= telebot.types.InlineKeyboardButton(btn_name+f"({size_formatted} MB)" , callback_data =call_back)

            quality_markup.add(quality_btn)

       try:
         bot.send_message(call.message.chat.id , "Available Qualiteis" , reply_markup=quality_markup)
       except:
         bot.send_message(call.message.chat.id ,"An Error Happend While Choosing.Please Make Sure You Are Choosing Only One Choice.")

    elif call.data in ["144p","240p","360p","480p","720p","1080p"] :

       bot.send_message(call.message.chat.id , f"Your video is being processed...\nget a cup of coffee if it's too large :)")
       VID = Download_Video(YOUTUBE_OBJ , call.data)

       # Send The Video
       Process = Send_Video(VID  , call.message.chat.id)

       if Process !="DONE":
          bot.send_message(call.message.chat.id , "An Error Happned While Downloading.Please Make Sure From Your Connection Or Try Later.")

       # Free up the memory
       os.remove(VID)

    # AUDIO
    elif call.data =="audio":

       bot.send_message(call.message.chat.id , f"Your Audio Is Being Processed...,Get A Cup Of Coffee If It's too large")
       AUD = Download_Audio(YOUTUBE_OBJ) # Download The Audio File
       Process = Send_Video(AUD  , call.message.chat.id) # Send The Audio

       if Process !="DONE":
          bot.send_message(call.message.chat.id , "An Error Happned While Downloading.Please Make Sure From Your Connection Or Try Later.")

    	# Free Up The Memory
       os.remove(AUD)

    # Remove The Keboard
    bot.edit_message_reply_markup(call.message.chat.id , call.message.message_id)


# Display A Help Msg
@bot.message_handler(commands = ["help"])
def help(message):

    HELP = '''-Enter The Commands /start
-Enter A Valid URL Of YouTube Video
-Choose Either You Want To Download
An Audio Or Video
-Only Files Less Than 500 MB Can Be Downloaded.
    '''
    bot.send_message(message.chat.id,HELP)

# Start The Bot
print("Bot Is Runing ............ ")
bot.polling()
