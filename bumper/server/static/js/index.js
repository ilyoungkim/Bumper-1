var elements = document.querySelectorAll("div[class^=thread]");
var snackbar = document.getElementById("snackbar");

function show_snackbar(message)
{
	snackbar.innerText = message;
	snackbar.className = 'show';
	setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 3000);
}

function save_defaults()
{
	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function()
	{
		if (this.readyState == 4)
		{
			data = JSON.parse(this.responseText);
			if (this.status == 200)
			{
				show_snackbar('Successfully updated configuration');
			}
			else if (this.status == 400)
			{
				show_snackbar(data['error']);
			}
			else
			{
				show_snackbar("Couldn't update the configuration");
				console.error(this.responseText);
			}
		}
	}

	var data = new FormData();
	data.append('bump_delay', document.querySelector('input[name=bump_delay]').textContent);
	data.append('post_delay', document.querySelector('input[name=post_delay]').textContent);
	data.append('default_message', document.querySelector('textarea[name=default_message]').value);

	xhr.open('POST', '/api/config', true);
	xhr.send(data);
}

function save_user()
{
	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function()
	{
		if (this.readyState == 4)
		{
			data = JSON.parse(this.responseText);
			if (this.status == 200)
			{
				show_snackbar('Successfully updated the user');
			}
			else if (this.status == 400)
			{
				show_snackbar(data['error']);
			}
			else
			{
				show_snackbar("Couldn't update the user");
				console.error(this.responseText);
			}
		}
	}

	var data = new FormData();
	data.append('username', document.querySelector('input[name=username]').value);
	data.append('old-password', document.querySelector('input[name=old-password]').value);
	data.append('new-password', document.querySelector('input[name=new-password]').value);

	xhr.open('POST', '/api/user', true);
	xhr.send(data);
}

function save_thread()
{
	var sel = document.querySelector("select[name=thread]");
	var selected = sel.options[sel.selectedIndex];
	var selected_info = document.querySelector("div[class=" + selected.className + "]");

	var message = selected_info.querySelector('textarea[name=message]');
	var name = selected_info.querySelector('input[name=name]');

	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function()
	{
		if (this.readyState == 4)
		{
			if (this.status == 200)
			{
				selected.textContent = name.value;
				show_snackbar('Successfully updated the thread');
			}
			else
			{
				show_snackbar("Couldn't update the thread");
				console.error(this.responseText);
			}
		}
	}

	var data = new FormData();
	data.append('method', 'edit');
	data.append('thread', selected.value);
	data.append('message', message.value);
	data.append('name', name.value);

	xhr.open('POST', '/api/thread', true);
	xhr.send(data);
}

function delete_thread()
{
	var sel = document.querySelector("select[name=thread]");
	var selected = sel.options[sel.selectedIndex];
	var selected_info = document.querySelector("div[class=" + selected.className + "]");

	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function()
	{
		if (this.readyState == 4)
		{
			if (this.status == 200)
			{
				for (var i = 0; i < elements.length; i++)
				{
					elements[i].style.display = 'none';
				}
				selected.parentNode.removeChild(selected);
				selected_info.parentNode.removeChild(selected_info);

				show_snackbar('Successfully deleted the thread');
			}
			else
			{
				show_snackbar("Couldn't delete the thread");
				console.error(this.responseText);
			}
		}
	}

	var data = new FormData();
	data.append('method', 'delete');
	data.append('thread', selected.value);

	xhr.open('POST', '/api/thread', true);
	xhr.send(data);
}

function change_info()
{
	var select = document.querySelector("select[name=thread]");
	var selected = select.options[select.selectedIndex];

	for (var i = 0; i < elements.length; i++)
	{
		if (elements[i].className == selected.className)
		{
			elements[i].style.display = 'inline';
		}
		else
		{
			elements[i].style.display = 'none';
		}
	}
}

function open_tab(evt, tabName)
{
	if (!document.getElementsByClassName(tabName)[0])
	{
		return;
	}

	window.document.title = 'Bumper :: ' + tabName.replace(/^\w/, c => c.toUpperCase());

	var content_tabs = document.getElementsByClassName('content-tab');
	var buttons = document.querySelectorAll('li > a');

	for (var i = 0; i < content_tabs.length; i++)
	{
		content_tabs[i].style.display = 'none';
	}

	for (var i = 0; i < buttons.length; i++)
	{
		if (buttons[i].className == 'is-active')
		{
			buttons[i].className = '';
		}
	}

	document.getElementsByClassName(tabName)[0].style.display = 'block';
	evt.currentTarget.className = 'is-active';
}