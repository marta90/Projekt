var ajax = new sack();

function loadContent(name) {
    $("#main-content").load("/media/html/"+name+".html");
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
    if (nickOk && indexOk)
        document.getElementById("btn_register").disabled = false;
    else
        document.getElementById("btn_register").disabled = true;
}
        
function checkUsername() {

//  document.getElementById("obrazek").className = "thinking";
    request = createRequest();
    if (request == null)
        alert("Unable to create request");
    else {
        var theName = document.getElementById("fld_loginCheck").value;
        var nick = escape(theName);
        var url= "/checkUsername/" + nick;
        request.onreadystatechange = showUsernameStatus;
        request.open("GET", url, true);
        request.send(null);
    }
}

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

function showIndexNumberStatus() {
    if (request.readyState == 4) {
        if (request.status == 200) {
            if (request.responseText == "okay") {
                //	document.getElementById("obrazek").className = "approved";
                indexOk = true;
                checkBoth();
            } else {
                indexOk = false;
                checkBoth();
                //	document.getElementById("obrazek").className = "denied";
                //	document.getElementById("fld_indexNumber").focus();
                //	document.getElementById("fld_indexNumebr").select();
            }
        }
    }
}

function giveSpec(faculty){
    if (document.getElementById('select_faculty').value=='0'){
        document.getElementById('select_specialization').disabled=true;
    }
    else {
        document.getElementById('select_specialization').disabled=false;
        var faculties = faculty.options[faculty.selectedIndex].value;
        findSpec(faculties);
    }
}

function findSpec(faculties){
    document.getElementById('select_specialization').options.length = 0;
    if(faculties.length>0){
	ajax.requestFile = "/giveSpecialization/" + faculties;
	ajax.onCompletion = makeSpec;
	ajax.runAJAX();
    }
}

function makeSpec(){
    var obj = document.getElementById('select_specialization');
    eval(ajax.response);
}

function checkName(){
    document.getElementById('fld_name').value
}



