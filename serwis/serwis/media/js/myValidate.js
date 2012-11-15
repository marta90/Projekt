function updateNameR()
{
    if (checkNameR())
        document.getElementById('fld_name').style.borderColor = '#c9c9c9 #d9d9d9 #e8e8e8';
    else
        document.getElementById('fld_name').style.borderColor = 'red';
}

function checkNameR()
{
    var valueF = document.getElementById('fld_name').value;
    var reg = /^([a-zA-Z '-]+)$/;
    return (reg.test(valueF) && valueF.length >=2)
}

function updateLastNameR()
{
    if (checkLastNameR())
        document.getElementById('fld_lastName').style.borderColor = '#c9c9c9 #d9d9d9 #e8e8e8';
    else
        document.getElementById('fld_lastName').style.borderColor = 'red';
}
function checkLastNameR()
{
    var valueF = document.getElementById('fld_lastName').value;
    var reg = /^([a-zA-Z '-]+)$/;
    return (reg.test(valueF) && valueF.length >=2)
}

function updatePassR()
{
    if (checkPassR())
        document.getElementById('fld_passF').style.borderColor = '#c9c9c9 #d9d9d9 #e8e8e8';
    else
        document.getElementById('fld_passF').style.borderColor = 'red';
}
function checkPassR()
{
   
    var valueF = document.getElementById('fld_passF').value;
    var reg = /^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$/;
    return (reg.test(valueF))
}

function updatePass2R()
{
    if (checkPass2R())
        document.getElementById('fld_passRepeat').style.borderColor = '#c9c9c9 #d9d9d9 #e8e8e8';
    else
        document.getElementById('fld_passRepeat').style.borderColor = 'red';
}
function checkPass2R()
{
    var valueF = document.getElementById('fld_passRepeat').value;
    var reg = /^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$/;
    return (reg.test(valueF));
}

function checkPassesR()
{
    var p1 = document.getElementById('fld_passF').value;
    var p2 = document.getElementById('fld_passRepeat').value;
    return (p1 == p2);
}

function checkBox1()
{
    return (document.getElementById('cbox_rules').checked);
}

function checkBox2()
{
    return (document.getElementById('cbox_permission').checked);
}

function checkBoxes()
{
    return (checkBox1() && checkBox2());
}

function updateBoxes()
{
    if(checkBox1())
    {
        document.getElementById('c1').style.backgroundColor = 'transparent';
    }
    else
    {
        document.getElementById('c1').style.backgroundColor = 'red';
    }
    if(checkBox2())
    {
        document.getElementById('c2').style.backgroundColor = 'transparent';
    }
    else
    {
        document.getElementById('c2').style.backgroundColor = 'red';
    }
}

function checkFormReg()
{
    updateNameR();
    updateLastNameR();
    updatePassR();
    updatePass2R();
    if(checkBox2())
    {
        document.getElementById('c2').style.backgroundColor = 'transparent';
    }
    if(checkBox1())
    {
        document.getElementById('c1').style.backgroundColor = 'transparent';
    }
    if(checkNameR() && checkLastNameR() && checkPassR() && checkPass2R())
    {
        if(checkPassesR())
        {
            if (checkBoxes())
                return true;
            else
            {
                updateBoxes();
                alert('Oznaczone pola są wymagane.')
                return false;
            }
        }
        else
        {
            alert('Hasła się od siebie różnią!')
            return false;
        }
    }
    else
   {
        alert('Wprowadzone dane nie spełniają wymaganych ograniczeń.')
        return false;
        
   }
}




/*


$(document).ready(function(){
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Imię"
    $('#fld_name').keyup(function() {
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        if($(this).val().length < 2){
            $(this).after("<div class='error' id='shortError'>Podane imię jest za krótkie</div>");
        }
        var reg = /^([a-zA-Z '-]+)$/;
        if(reg.test($(this).val()) == false){
            $(this).after("<div class='error' id='shortError'>Wprowadź imię poprawnie!</div>");
        }
    });
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Nazwisko"
    $('#fld_lastName').keyup(function() {
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        if($(this).val().length < 2){
            $(this).after("<div class='error' id='shortError'>Podane nazwisko jest za krótkie</div>");
        }
        var reg = /^([a-zA-Z '-]+)$/;
        if(reg.test($(this).val()) == false){
            $(this).after("<div class='error' id='shortError'>Wprowadź nazwisko poprawnie!</div>");
        }
        
    });
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Hasło"
    $('#fld_pass').keyup(function() {
        // usuwanie errorsow
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        var threeRepeatChars = /^(?!.*(.)\1{3}).*$/ //ponad trzy takie same znaki pod rząd
        var numbSpecChar = /^((?=.*[\d])|(?=.*[^\w\d\s])).*$/ //numery i specjalne znaki
        var longChars = /^(?=.*[A-Z]).*$/ //duze znaki
        var smallChars = /^(?=.*[a-z]).*$/ //male znaki
        var reg = /^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$/;
        
        if(reg.test($(this).val()) == false){
            if($(this).val().length < 8){
                $(this).after("<div class='error' id='shortError'>Hasło jest za krótkie.</div>");
            }
            if(threeRepeatChars.test($(this).val()) == false){
                $(this).after("<div class='error' id='shortError'>W haśle występują pod rząd trzy takie same znaki</div>");
            }
            if(numbSpecChar.test($(this).val()) == false){
                $(this).after("<div class='error' id='shortError'>Hasło powinno zawierać cyfry lub specjalne znaki</div>");
            }
            if(longChars.test($(this).val()) == false){
                $(this).after("<div class='error' id='shortError'>Hasło powinno zawierać duże znaki</div>");
            }
            if(smallChars.test($(this).val()) == false){
                $(this).after("<div class='error' id='shortError'>Hasło powinno zawierać małe znaki</div>");
            }
            if($(this).val().length > 20){
                $(this).after("<div class='error' id='shortError'>Hasło jest za długie.</div>");
            }
            //$(this).after("<div class='error' id='shortError'>Hasło powinno zawierać małe i wielkie litery oraz cyfry lub znaki specjalne!</div>");
        }
    });
    // Zdarzenie nastepujace po straceniu focusa dla pola "Powtórz hasło"
    $('#fld_passRepeat').focusout(function() {
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        if($(this).val() != $('#fld_pass').val()){
            $(this).after("<div class='error' id='shortError'>Powtórzone hasło nie jest poprawne.</div>");
        }
    });
});*/