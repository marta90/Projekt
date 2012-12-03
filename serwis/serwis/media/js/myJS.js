//var ajax = new sack();

function loadContent(name) {
    $("#main-content").load("/media/html/"+name+".html");
    
    /*
    $("#portal-shoutbox-scroll").getNiceScroll().resize().hide();
	$("#portal-important-msgs-scroll").getNiceScroll().resize().hide();
	$("#portal-my-events-scroll").getNiceScroll().resize().hide();
	$("#portal-new-events-scroll").getNiceScroll().resize().hide();
    $("#map-scroll").getNiceScroll().resize().hide();
    $("#calendar-scroll").getNiceScroll().resize().hide();
    $("#teachers-scroll").getNiceScroll().resize().hide();
    $("#timetable-scroll").getNiceScroll().resize().hide();
    */
    return false;
}

function loadContentAfter(name, funct) {
    $("#main-content").load("/media/html/"+name+".html", funct);
    return false;
}

function createRequest() {
    try {
        request = new XMLHttpRequest();
    } catch (tryMS) {
        try {
            request = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (otherMS) {
            try {
                request = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (failed) {
                request = null;
            }
        }
    }
    return request;
}

function clearField(id) {
    document.getElementById(id).value = "";
}

function checkButton() {
    var p1 = document.getElementById('obrazek').className;
    var p2 = document.getElementById('obrazek2').className;
    var p3 = document.getElementById('obrazek3').className;
    var p4 = document.getElementById('obrazek4').className;
    
    if (p1 == 'approved' && p2== 'approved' && p3 == 'approved' && p4 == 'approved')
        document.getElementById("btn_register").disabled = false;
    else
    {
        
        document.getElementById("btn_register").disabled = true;
    }
}


// Pobranie kierunków z okreslonego wydziału - funkcja wysyłająca zapytanie do serwera
function checkUsername() {
    var theName = document.getElementById("fld_loginCheck").value;
    request = createRequest();
    if (request == null)
        alert("Unable to create request");
    else {
        var nick = escape(theName);
        var url= "/checkUsername/" + nick;
        request.onreadystatechange = showUsernameStatus;
        request.open("GET", url, true);
        request.send(null);
    }
}
// Sprawdzanie czy istnieje użytkownik o takim loginie w systemie - odebranie odpowiedzi od serwera
function showUsernameStatus() {
    if (request.readyState == 4) {
        if (request.status == 200) {
            if (request.responseText == "okay") {
            	document.getElementById("obrazek2").className = "approved";
              
            } else {
            	document.getElementById("obrazek2").className = "denied";
            }
            checkButton();
        }
    }
}

// Sprawdzanie czy istnieje użytkownik o takim indeksie w systemie - wyslanie zapytania do serwera
function checkIndexNumber() {
    request = createRequest();
    if (request == null)
        alert("Unable to create request");
    else {
        var ind = document.getElementById("fld_indexNumber").value;
        var index = escape(ind);
        var url= "/checkIndexNumber/" + index;
        request.onreadystatechange = showIndexNumberStatus;
        request.open("GET", url, true);
        request.send(null);
    }
}

// Sprawdzanie czy istnieje użytkownik o takim indeksie w systemie - odebranie odpowiedzi od serwera
function showIndexNumberStatus() {
    if (request.readyState == 4) {
        if (request.status == 200) {
            if (request.responseText == "okay") {
                document.getElementById("obrazek4").className = "approved";
                
            } else {
                document.getElementById("obrazek4").className = "denied";
            }
            checkButton();
        }
    }
}

function selectItemByValue(elmnt, value)
{
    var el = document.getElementById(elmnt);
    for(var i=0; i < el.options.length; i++)
    {
        if(el.options[i].value == value)
            el.selectedIndex = i;
    }
}

function selectedOption(selectFieldName)
{
    var selectFld = document.getElementById(selectFieldName);
    var val = selectFld.options[selectFld.selectedIndex].value;
    return val;
}


// Get specializations from server
function getSpecializationsRegister(faculties)
{
	ajax = new sack();
	var faculty = faculties.options[faculties.selectedIndex].value;
	document.getElementById('select_specialization').options.length = 0;
	if(faculty.length>0)
	{
		ajax.requestFile = "/giveSpecialization/" + faculty;
		ajax.onCompletion = createSpecializations;
		ajax.runAJAX();
	}
}


// Get specializations from server
function getSpecializations(faculties)
{
	ajax = new sack();
    var select_fac = faculties.id;
	var faculty = faculties.options[faculties.selectedIndex].value;
    facultyNumber = select_fac.substring(14);
    var select_spec = 'select_specialization' + facultyNumber;

	document.getElementById(select_spec).options.length = 0;
	if(faculty.length>0)
	{
		ajax.requestFile = "/giveSpecialization/" + faculty;
		ajax.onCompletion = createSpecializations;
		ajax.runAJAX();
	}
}

// Create select box with specializations
function createSpecializations()
{
    
	var obj = document.getElementById('select_specialization' + facultyNumber);
	eval(ajax.response);
	getSemesters(obj);
}

// Get semesters from server
function getSemesters()
{
	ajax = new sack();
	var spec = document.getElementById('select_specialization' + facultyNumber);
    var type = document.getElementById('select_type' + facultyNumber);
    var sp = spec.options[spec.selectedIndex].value;
    var tp = type.options[type.selectedIndex].value;
	document.getElementById('select_semester' + facultyNumber).options.length = 0;
	if(sp.length>0 && tp.length>0)
	{
		ajax.requestFile = "/giveSemester/" + sp + "/" + tp;
		ajax.onCompletion = createSemesters;
		ajax.runAJAX();
	}
	
}

// Create select box with semesters
function createSemesters()
{
	var obj = document.getElementById('select_semester' + facultyNumber);
	eval(ajax.response);
}

//Show content picked in left block
function showChoice(myChoice)
{

	var timetableDiv = document.getElementById('timetable_account');
	var settingsDiv = document.getElementById('settings_account');
	var adminDiv = document.getElementById('administration_account');
    var specializationDiv = document.getElementById('specs_account');

	myChoice.id == "acc-timetable" ? timetableDiv.style.display='block' : timetableDiv.style.display='none';
	myChoice.id == "acc-settings" ? settingsDiv.style.display='block' : settingsDiv.style.display='none';
	myChoice.id == "acc-admin" ? adminDiv.style.display='block' : adminDiv.style.display='none';
    myChoice.id == "acc-specs" ? specializationDiv.style.display='block' : specializationDiv.style.display='none';
}

//Limit character to 250, update char left and button
function checkTextarea()
{
	var max = 250;
	var size = document.getElementById('textarea_request').value.length;
	if (size == 0)
		document.getElementById('btn_request').disabled = true;
	else
		document.getElementById('btn_request').disabled = false;
	if (size>max)
		document.getElementById('textarea_request').value = document.getElementById('textarea_request').value.substring(0,max);
	var charLeft = max-size;
	if (charLeft<0)
		charLeft = 0;
	document.getElementById('textarea_request_char').value = charLeft +"/250";
}
function zrobGodzine(godz, min){
    var godz2 = "";
    var min2 = "";
    if(godz.length == 1){
        godz2 = '0'+godz; 
    } else {godz2=godz;}
     if(min.length == 1){
        min2 = '0'+min; 
    } else {min2=min;}
    return godz2+':'+min2;
}


Date.prototype.getTydzien = function () {
      var cel = new Date(this.valueOf());
      var dayNr = (this.getDay() + 6) % 7;
      cel.setDate(cel.getDate() - dayNr + 3);
      var sty4 = new Date(cel.getFullYear(), 0, 4);
      var sty4DayNr = (sty4.getDay() + 6) % 7;
      sty4.setDate(sty4.getDate() - sty4DayNr + 3);
      var dayDiff = (cel - sty4) / 86400000;
      var numertygodnia = 1 + Math.floor(Math.floor(Math.abs(dayDiff)) / 7);
      return numertygodnia;
}

