$(document).ready(function(){
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Imię"
    $('#fld_name').keyup(function() {
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        if($(this).val().length < 3){
            $(this).after("<div class='error' id='shortError'>Podane imię jest za krótkie</div>");
        }
        var reg = /^(([A-za-z]+[\s]{1}[A-za-z]+)|([A-Za-z]+))$/;
        if(reg.test($(this).val()) == false){
            $(this).after("<div class='error' id='shortError'>Wprowadź imię poprawnie!</div>");
        }
    });
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Nazwisko"
    $('#fld_lastName').keyup(function() {
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        if($(this).val().length < 3){
            $(this).after("<div class='error' id='shortError'>Podane nazwisko jest za krótkie</div>");
        }
        var reg = /^(([A-za-z]+[\s]{1}[A-za-z]+)|([A-Za-z]+))$/;
        if(reg.test($(this).val()) == false){
            $(this).after("<div class='error' id='shortError'>Wprowadź imię poprawnie!</div>");
        }
        
    });
    // Zdarzenie nastepujace po nacisnieciu klawisz dla pola "Hasło"
    $('#fld_pass').keyup(function() {
        // usuwanie errorsow
        if ($(this).parent().find('.error').length > 0){
            $(this).parent().find('.error').remove();
        }
        var threeRepeatChars = /^(?!.*(.)\1{3}).*$/ //trzy takie same znaki pod rząd
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
});