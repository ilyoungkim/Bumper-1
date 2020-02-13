from bumper.bumper import Bumper

client = Bumper('user', 'pass')

client.reply('123456', 'I am replying to a thread')

client.logout()