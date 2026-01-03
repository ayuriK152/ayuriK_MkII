import discord
from discord.ext import commands
import pandas as pd
import numpy
import os
import platform
import requests
from PIL import Image, ImageSequence


############
# 전역 변수 #
############

# 디스코드 봇 구동용
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
botActivity = discord.Game('수용소 감시')

workDir = ''
if platform.system()!='Windows':
    workDir = os.getcwd()+'/'

channelCsv = pd.read_csv(workDir+'Datas/ChannelList.csv', encoding='UTF-8')
reactionMsgCsv = pd.read_csv(workDir+'Datas/ReactionMsgLists.csv', encoding='UTF-8')
# onewayRoleCsv = pd.read_csv(workDir+'Datas/OnewayRoleList.csv', encoding='UTF-8')

imageTransferTypes = ['webp', 'jfif']

#############
# 일반 메소드 #
#############

# webp형식일 때 애니메이션이 있는지 확인
def is_animated_media(media):
    index = 0

    for frame in ImageSequence.Iterator(media):
        index += 1
    
    if index > 1:
        return True
    else:
        return False


def log(msg):
    print('[system]: '+msg)


###############
# 비동기 메소드 #
###############

# 명령어 양식 검증
async def command_param_count(ctx, len, min, max):
    if len < min:
        await ctx.send(f'에러. 명령어 인자가 너무 적습니다.')
        return -1
    elif len > max:
        await ctx.send(f'에러. 명령어 인자가 너무 많습니다.')
        return 1
    return 0


# 봇 초기화, 시작할 때 한 번 실행
async def init():
    channelIds = channelCsv['channel_id'].values
    for i in range(channelIds.size):
        guild = bot.get_guild(channelCsv[channelCsv['channel_id']==numpy.int64(channelIds[i])]['guild_id'].values[0])
        channel = guild.get_channel(channelIds[i])
        msgIds = reactionMsgCsv[reactionMsgCsv['channel_id']==numpy.int64(channelIds[i])]['message_id'].values
        for j in range(msgIds.size):
            await channel.get_partial_message(msgIds[j]).add_reaction('✅')
            await channel.get_partial_message(msgIds[j]).add_reaction('❌')


####################
# 봇 실제 기능 메소드 #
####################

# 봇 시작
@bot.event
async def on_ready():
    log('아유릭 MkII 출격')
    await bot.change_presence(status=discord.Status.online, activity=botActivity)
    await init()


# 이모지 반응 역할 부여 메소드
@bot.event
async def on_raw_reaction_add(ctx):
    if ctx.member.bot:
        return
    
    guild = bot.get_guild(ctx.guild_id)
    channelId = channelCsv[channelCsv['guild_id']==numpy.int64(ctx.guild_id)]['channel_id'].values
    messageId = reactionMsgCsv[reactionMsgCsv['message_id']==numpy.int64(ctx.message_id)]['message_id'].values

    if channelId.size == 0:
        log('channel.size == 0')
        return
    if messageId.size == 0:
        log('messageId.size == 0')
        return
    
    for i in range(channelId.size):
        try:
            channel = guild.get_channel(channelId[i])
            role = guild.get_role(reactionMsgCsv[reactionMsgCsv['message_id'] == numpy.int64(ctx.message_id)]['role_id'].values[0])

            if str(ctx.emoji.name) == '✅':
                await channel.get_partial_message(ctx.message_id).remove_reaction('✅', ctx.member)
                await ctx.member.add_roles(role)
            elif str(ctx.emoji.name) == '❌':
                await channel.get_partial_message(ctx.message_id).remove_reaction('❌', ctx.member)
                await ctx.member.remove_roles(role)
            break
        except:
            continue


#################
# 명령어 작동 기능 #
#################

# 도움말 (추가 예정)
@bot.command(name="명령어")
async def help(ctx):
    await ctx.send('안녕이나 치세요')


# 잡다한 명령어
@bot.command(name="안녕")
async def hello(ctx):
    await ctx.send('안녕하세요')


# 이미지 인식 후 png, gif 변환 (기능 사용 일시 중단)
# 1. 요즘 webp 로컬에서 잘 열리는거 같은데 굳이 필요한 기능인가 싶음.
# 2. gif 변환 불안정, 용량 제한 등 문제가 더 많음.
# @bot.event
# async def on_message(message):
#     await bot.process_commands(message)

#     if message.author.bot:
#         return
    
#     # 첨부파일 없는경우 스킵
#     if len(message.attachments) <= 0:
#         return
    
#     extension = message.attachments[0].filename.split('.')[-1]

#     # 변환 대상 확장자인지 확인 (webp, jfif)
#     if any(extension in s for s in imageTransferTypes):
#         url = message.attachments[0].url
#         img = Image.open(requests.get(url, stream = True).raw)

#         if (is_animated_media(img) == False or extension == 'jfif'):
#             img.save('Temp/temp.png', format='png')
#             await message.channel.send('이미지 변환 완료! (' + extension + ' -> png)', file = discord.File('Temp/temp.png'))
#         else:
#             frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
#             img.save('Temp/temp.gif', format='gif', save_all = True, append_images = frames)
#             fileSize = os.path.getsize('Temp/temp.gif') / (1024 * 1024)
#             print(fileSize)
#             if fileSize > 25:
#                 await message.channel.send('변환된 이미지의 파일이 너무 커요..')
#             else:
#                 await message.channel.send('이미지 변환 완료! (webp -> gif)', file = discord.File('Temp/temp.gif'))


#####################################################
# 어드민 전용 기능들 || 도움말에 사용법이 노출되어선 안됨   #
# 명령어 입력한 사람이 어드민인지 확인하는 기능도 추가 고려 #
#####################################################

# 역할자판기 채널 등록
@bot.command(name='역할자판기-채널등록')
async def register_role_channel(ctx, *args):
    global channelCsv
    
    if await command_param_count(ctx, len(args), 1, 1) != 0:
        return

    channelId = args[0].split('/')[-1]

    if channelCsv[channelCsv['channel_id'] == numpy.int64(channelId)]['channel_id'].values.size != 0:
        await ctx.send(f'{args[0]}: 해당 채널은 이미 역할자판기 채널로 등록되어있습니다.')
        return
    
    channelCsv = pd.concat([channelCsv, pd.DataFrame({'guild_id' : [ctx.guild.id], 'channel_id' : [channelId]})])
    channelCsv.to_csv('Datas/ChannelList.csv', mode='w', index=None)
    await ctx.send(f'{args[0]}: 해당 채널을 역할자판기 채널로 등록했습니다.')


# 역할자판기 메세지 할당
@bot.command(name='역할자판기-추가')
async def add_role(ctx, *args):
    global reactionMsgCsv, channelCsv
    
    if await command_param_count(ctx, len(args), 2, 2) != 0:
        return
    
    guildId = ctx.guild.id
    channelId = channelCsv[channelCsv['guild_id'] == numpy.int64(guildId)]['channel_id'].values[0]

    if channelId is None:
        await ctx.send(f'본 서버에 등록된 역할자판기용 채널이 하나도 존재하지 않습니다. `/역할자판기-채널등록` 명령어를 사용해서 채널 등록을 먼저 진행해주세요.')
        return
    
    inputMsgId = args[0].split('/')[-1]
    inputRoleId = args[1][3:-1]

    if reactionMsgCsv[reactionMsgCsv['message_id'] == numpy.int64(inputMsgId)]['message_id'].values.size > 0:
        await ctx.send(f'{args[0]}: 해당 메세지는 이미 역할자판기 메세지로 등록되어있습니다.')
        return
    
    if reactionMsgCsv[reactionMsgCsv['role_id'] == numpy.int64(inputRoleId)]['role_id'].values.size > 0: 
        await ctx.send(f'{args[1]}: 해당 역할은 이미 역할자판기에 등록되어있습니다.')
        return
    
    pd.concat([reactionMsgCsv, pd.DataFrame({'channel_id' : [channelId], 'message_id' : [inputMsgId], 'role_id' : [inputRoleId]})]).to_csv('Datas/ReactionMsgLists.csv', mode='w', index=None)
    reactionMsgCsv = pd.read_csv('Datas/ReactionMsgLists.csv', encoding='UTF-8')

    guild = bot.get_guild(guildId)
    channel = guild.get_channel(channelId)

    await channel.get_partial_message(inputMsgId).add_reaction('✅')
    await channel.get_partial_message(inputMsgId).add_reaction('❌')
    await ctx.send(f'{args[0]} {args[1]}: 해당 메세지와 역할을 역할자판기에 등록했습니다.')


# 봇 실행    
bot.run(open('TOKEN.txt', "r").read())