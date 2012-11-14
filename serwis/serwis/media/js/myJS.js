//var ajax = new sack();

function loadContent(name) {
    $("#main-content").load("/media/html/"+name+".html");
    $("#portal-shoutbox-scroll").getNiceScroll().resize().hide();
	$("#portal-important-msgs-scroll").getNiceScroll().resize().hide();
	$("#portal-my-events-scroll").getNiceScroll().resize().hide();
	$("#portal-new-events-scroll").getNiceScroll().resize().hide();
    $("#map-scroll").getNiceScroll().resize().hide();
    $("#calendar-scroll").getNiceScroll().resize().hide();
    $("#teachers-scroll").getNiceScroll().resize().hide();
    $("#timetable-scroll").getNiceScroll().resize().hide();
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

// Get specializations from server
function getSpecializationsRegister(faculties)
{
	ajax = new sack();
	var faculty = faculties.options[faculties.selectedIndex].value;
    if(faculty == 0)
        document.getElementById('select_specialization')
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
	var faculty = faculties.options[faculties.selectedIndex].value;
	document.getElementById('select_specialization').options.length = 0;
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
	var obj = document.getElementById('select_specialization');
	eval(ajax.response);
	if (firstSpec)
	{
		selectItemByValue('select_specialization', specializationSt);
		firstSpec = false;
	}
	getSemesters();
}

// Get semesters from server
function getSemesters()
{
	ajax = new sack();
	var spec = document.getElementById('select_specialization');
    var type = document.getElementById('select_type');
    var sp = spec.options[spec.selectedIndex].value;
    var tp = type.options[type.selectedIndex].value;
	document.getElementById('select_semester').options.length = 0;
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
	var obj = document.getElementById('select_semester');
	eval(ajax.response);
	if(firstSem)
	{
		selectItemByValue('select_semester', semesterSt);
		selectItemByValue('select_type', levelSt);
		firstSem = false;
	}
}

//Show content picked in left block
function showChoice(myChoice)
{
	document.getElementById('acc-settings').setActive();
	var timetableDiv = document.getElementById('timetable_account');
	var settingsDiv = document.getElementById('settings_account');
	var adminDiv = document.getElementById('administration_account');

	myChoice.id == "acc-timetable" ? timetableDiv.style.display='block' : timetableDiv.style.display='none';
	myChoice.id == "acc-settings" ? settingsDiv.style.display='block' : settingsDiv.style.display='none';
	myChoice.id == "acc-admin" ? adminDiv.style.display='block' : adminDiv.style.display='none';
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

/*



// Pobranie kierunków z okreslonego wydziału - pobranie i uruchomienie funkcji szukania
function giveSpec(faculty){
    document.getElementById('select_semester').disabled=true;
    if (faculty.value=='0'){
        document.getElementById('select_specialization').disabled=true;
        document.getElementById('select_type').disabled=true;
    }
    else {
        document.getElementById('select_specialization').disabled=false;
        document.getElementById('select_type').disabled=false;
        var faculties = faculty.options[faculty.selectedIndex].value;
        findSpec(faculties);
        findSem();      // szukanie liczby semestrów
    }
}

// Pobranie kierunków z okreslonego wydziału - funkcja wysyłająca zapytanie do serwera
function findSpec(faculties){
    document.getElementById('select_specialization').options.length = 0;
    document.getElementById('select_semester').options.length = 0;
    if(faculties.length>0){
        request = createRequest();
        if (request == null)
            alert("Unable to create request");
        else {
            var url= "/giveSpecialization/" + faculties;
            request.onreadystatechange = makeSpec;
            request.open("GET", url, true);
            request.send(null);
        }   
    }
}


// Pobranie kierunków z okreslonego wydziału - odebranie odpowiedzi i utworzenie obiektu SELECT
function makeSpec(){
    if (request.readyState == 4) {
        if (request.status == 200) {
            var obj = document.getElementById('select_specialization');
            var iexplorer = navigator.appName == "Microsoft Internet Explorer" ? true : false ; //Verifiy explorer
            if (iexplorer) {
                alert('To explorer');
                
                str2 = 'x' + request.responseText; // Super very very important
                xparent = obj.parentElement;
                obj.innerHTML = '';
                obj.innerHTML = str2;
                xparent.innerHTML = obj.outerHTML;
                obj.text = '' + request.responseText;
            } else {
                alert('x');
                obj.innerHTML = '' + request.responseText;
            }
        }
    }
}

// Pobranie liczby semestrów z danego wydzialu - wyslanie zapytania do serwera
function findSem(){
    var spec = document.getElementById('select_specialization');
    var type = document.getElementById('select_type');
    
    var specialization = spec.options[spec.selectedIndex].value;
    var types = type.options[type.selectedIndex].value;

    document.getElementById('select_semester').options.length = 0;
    if (specialization != 0){
        document.getElementById('select_semester').disabled=false;
        if(specialization.length>0 && types.length>0){
            request = createRequest();
            if (request == null)
                alert("Unable to create request");
            else {
                var url= "/giveSemester/" + specialization + "/" + types;
                request.onreadystatechange = makeSem;
                request.open("GET", url, true);
                request.send(null);
            }  
        }
    } else {
        document.getElementById('select_semester').disabled=true;
    }
}

// Pobranie liczby semestrów z danego wydzialu - odebranie zapytania od serwera
function makeSem(){
    if (request.readyState == 4) {
        if (request.status == 200) {
            var obj = document.getElementById('select_semester');
            var iexplorer = navigator.appName == "Microsoft Internet Explorer" ? true : false ; //Verifiy explorer
            if (iexplorer) {
                str2 = 'x' + request.responseText; // Super very very important
                xparent = obj.parentElement;
                obj.innerHTML = '';
                obj.innerHTML = str2;
                xparent.innerHTML = obj.outerHTML;
            } else {
                obj.innerHTML = '' + request.responseText;
            }
        }
    }
}




//Show content picked in left block
function showChoice(myChoice)
{
	var timetableDiv = document.getElementById('timetable_account');
	var settingsDiv = document.getElementById('settings_account');
	var adminDiv = document.getElementById('administration_account');

	myChoice.id == "acc-timetable" ? timetableDiv.style.display='block' : timetableDiv.style.display='none';
	myChoice.id == "acc-settings" ? settingsDiv.style.display='block' : settingsDiv.style.display='none';
	myChoice.id == "acc-admin" ? adminDiv.style.display='block' : adminDiv.style.display='none';
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

//Update specializations when faculty has been changed
function refreshSpecializations()
{
	var faculties = document.getElementById('select_faculty');
	faculty = faculties.options[faculties.selectedIndex].value;
	if (faculty.length>0)
	{
		request = createRequest();
		if (request == null)
			alert("Unable to create request");
		else
		{
			var url= "/giveSpecialization/" + faculty;
			request.onreadystatechange = function()
			{
				if (request.readyState == 4)
				{
					if (request.status == 200)
					{
						var obj = document.getElementById('select_specialization');
                        
						var iexplorer = navigator.appName == "Microsoft Internet Explorer" ? true : false ;
						if (iexplorer)
						{
                            alert('Explorer');
							str2 = 'x' + request.responseText; // Super very very important
							xparent = obj.parentElement;
							obj.innerHTML = '';
							obj.innerHTML = str2;
							xparent.innerHTML = obj.outerHTML;
						}
						else
						{
							obj.innerHTML = '' + request.responseText;
							if (firstSpec)
							{
								selectItemByValue('select_specialization', specializationSt);
								firstSpec = false;
							}
							refreshSemesters();
						}
					}
				 }
			};
			request.open("GET", url, true);
			request.send(null);
		}   
	}
}

//Update semesters when faculty, level or sepcialization has benn changed
function refreshSemesters()
{
	var levels = document.getElementById('select_type');
	level = levels.options[levels.selectedIndex].value;
	var specializations = document.getElementById('select_specialization');
	specialization = specializations.options[specializations.selectedIndex].value;
	if (specialization.length>0 && level.length>0)
	{
		request = createRequest();
		if (request == null)
			alert("Unable to create request");
		else
		{
			var url= "/giveSemester/" + specialization + "/" + level;
			request.onreadystatechange = function()
			{
				if (request.readyState == 4)
				{
					if (request.status == 200)
					{
						var obj = document.getElementById('select_semester');
						var iexplorer = navigator.appName == "Microsoft Internet Explorer" ? true : false ; //Verifiy explorer
						if (iexplorer)
						{
                            
							str2 = 'x' + request.responseText; // Super very very important
							xparent = obj.parentElement;
							obj.innerHTML = '';
							obj.innerHTML = str2;
							xparent.innerHTML = obj.outerHTML;
						}
						else
						{
							obj.innerHTML = '' + request.responseText;
							if (firstSem)
							{
								selectItemByValue('select_semester', semesterSt);
								selectItemByValue('select_type', levelSt);
								firstSem = false;
							}
						}
					}
				}
			};
			request.open("GET", url, true);
			request.send(null);
		}   
	}
}
  */