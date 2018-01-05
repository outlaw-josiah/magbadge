var res_box	= document.getElementById('response')
var button	= document.getElementById('button')
var input	= document.getElementById('badgeID')
console.log(res_box.innerHTML)

function tBox_keydown(element, event) {
	if (event.keyCode == 13) {
		button.click()
		element.select()
	}
}


var socket = new WebSocket("ws://localhost:28000/")
socket.onmessage = function(response) {
	data = JSON.parse(response.data)
	if (data.status == 200){
		data = data.result
		var res_final = "[" + data.badge_num + "] " +
						data.badge_t + ", " +
						data.ribbons + "<br>" +
						data.name + " has worked " +
						data.hr_worked + " of " +
						data.hr_total + " hours. <br>"
		res_box.innerHTML = res_final
	} else {
		res_box.innerHTML = data.error
	}
}
socket.onclose = function(event) {
	res_box.innerHTML = "Socket closed, please refresh. Here's some data:<br>" +
						"Close code: " + event.code +
						" | Close clean: " + (event.wasClean ? "Yes" : "No") + "<br>" +
						"Close reason: " + event.reason + "<br>"
	button.disabled = true
}


function sendBadge() {
	console.log(input.value)
	data = {action	: "query.badge",
			params	: isNaN(input.value) ? input.value : parseInt(input.value)}
	res_box.innerHTML = "Checking badge..."
	socket.send(JSON.stringify(data))
}
button.disabled = false
