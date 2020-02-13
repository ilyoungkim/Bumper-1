from bumper.bumper import Bumper

client = Bumper('user', 'pass')

alerts = client.alerts()
messages = client.messages()

print('Alerts')
for alert in alerts:
	print(f"[{alert['time']}] {alert['user']}: {alert['info']}")

print('Messages')
for message in messages:
	print(f"[{alert['time']}] {alert['user']}: {alert['title']}")

client.logout()