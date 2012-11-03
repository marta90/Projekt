//var ajax = new sack();

function loadContent(name) {
    $("#main-content").load("/media/html/"+name+".html");
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

function checkBoth() {
    if ($('#btn_register').parent().find('.error').length > 0){
	$('#btn_register').parent().find('.error').remove();
    }
    if (nickOk && indexOk){
        document.getElementById("btn_register").disabled = false;
    }
    else{
        $('#btn_register').after("<div class='error' id='shortError'>Użytkownik istnieje już w systemie.</div>");
        document.getElementById("btn_register").disabled = true;
    }
}

// Pobranie kierunków z okreslonego wydziału - funkcja wysyłająca zapytanie do serwera
function checkUsername() {
    var theName = document.getElementById("fld_loginCheck").value;
//  document.getElementById("obrazek").className = "thinking";
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
            //	document.getElementById("obrazek").className = "approved";
                nickOk = true;
                checkBoth();
            } else {
                nickOk = false;
                checkBoth();
            //	document.getElementById("obrazek").className = "denied";
            //	document.getElementById("fld_loginCheck").focus();
            //	document.getElementById("fld_loginCheck").select();
            }
        }
    }
}

// Sprawdzanie czy istnieje użytkownik o takim indeksie w systemie - wyslanie zapytania do serwera
function checkIndexNumber() {
//  document.getElementById("obrazek").className = "thinking";
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
                indexOk = true;
                checkBoth();
            } else {
                indexOk = false;
                checkBoth();
            }
        }
    }
}

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

