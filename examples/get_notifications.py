from bumper.bumper import Bumper

client = Bumper('user', 'pass')

alerts = client.alerts()
messages = client.messages()

for alert in alerts:
	print(f"[{alert['time']}] {alert['user']}: {alert['info']}")

for message in messages:
	print(f"[{message['time']}] {message['user']}: {message['title']}")

client.logout()