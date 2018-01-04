var status_box	= document.getElementById('response')
var button		= document.getElementById('button')
var input		= document.getElementById('badgeID')
var d_bnum		= document.getElementById('BNUM').children[1]
var d_name		= document.getElementById('NAME').children[1]
var d_btext		= document.getElementById('BTEXT').children[1]
var d_hours		= document.getElementById('HOURS').children
var d_btype		= document.getElementById('BTYPE').children[1]
var d_ribbons	= document.getElementById('RIBBONS').children[1]
var d_sandwich	= document.getElementById('SANDWICH').children[1]
var r_vegan		= document.getElementById('VEGAN').children[1]
var r_pork		= document.getElementById('PORK').children[1]
var r_gluten	= document.getElementById('GLUTEN').children[1]
var r_nuts		= document.getElementById('NUTS').children[1]
var r_freeform	= document.getElementById('FREEFORM').children[1]

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
		d_bnum.textContent	= data.badge_num
		d_name.textContent	= data.name
		d_btext.textContent	= data.btext
		d_hours[1].textContent = data.hr_worked
		d_hours[2].textContent = data.hr_total
		d_btype.textContent = data.badge_t
		d_ribbons.textContent = data.ribbons
		d_name.textContent = data.name
		d_sandwich.textContent = data.sandwich

		r_freeform.textContent = data.restrict[0]
		status_box.innerHTML = "Done"
	} else {
		status_box.innerHTML = data.error
	}
}
socket.onclose = function(event) {
	status_box.innerHTML = "Socket closed, please refresh. Here's some data:<br>" +
						"Close code: " + event.code +
						" | Close clean: " + (event.wasClean ? "Yes" : "No") + "<br>" +
						"Close reason: " + event.reason + "<br>"
	button.disabled = true
}


function sendBadge() {
	data = {action	: "query.badge",
			params	: isNaN(input.value) ? input.value : parseInt(input.value)}
	status_box.innerHTML = "Checking badge..."
	socket.send(JSON.stringify(data))
}
button.disabled = false
