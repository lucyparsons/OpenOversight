$(document).ready(function() {
    var emailfield = document.getElementById('email');
    var userfield = document.getElementById('username');
    var oldpasswdfield = document.getElementById('old_password');
    var password = document.getElementById('password');
    var password2 = document.getElementById('password2');
    var meter = document.getElementById('password-strength-meter');
    var meter2 = document.getElementById('password-confirmation-meter');
    var text = document.getElementById('password-strength-text');
    var submit = $('#password-button');

    function check_confirmation() {
        var val1 = password.value;
        var val2 = password2.value;
        if (val2 !== "") {
            if (val1 == val2) {
                meter2.value = 5;
                $(meter2).removeClass("badmeter").addClass("goodmeter");
                return true ;
            } else {
                meter2.value = 5;
                $(meter2).removeClass("goodmeter").addClass("badmeter");
                return false ;
            }
        } else {
            meter2.value = 0;
            return false ;
        }
    }

    function validate_form() {
        valid = true ;
        if ((emailfield != undefined) && (emailfield.value == "" )) {
            valid = false ;
        }
        if ((userfield != undefined) && (userfield.value == "")) {
            valid = false ;
        }
        if ((oldpasswdfield != undefined) && (oldpasswdfield.value == "")) {
            valid = false ;
        }
        if (meter.value < 3) {
            valid = false ;
        }
        if (!check_confirmation()) {
            valid = false ;
        }
        if (valid) {
            submit.attr("disabled", false);
        } else {
            submit.attr("disabled", true);
        }
        return valid ;
    }

    password.addEventListener('input', function() {
        var val = password.value;
        var result = zxcvbn(val);
        meter.value = result.score +1;
        if (val !== "") {
            if (meter.value < 3) {
                text.innerHTML = "Password not strong enough";
            } else {
                text.innerHTML = "OK";
            }
        } else {
            text.innerHTML = "";
            meter.value = 0;
        }
        validate_form();
    });
    password2.addEventListener('input', function() {
        validate_form();
    });
    if (emailfield != undefined) {
        emailfield.addEventListener('input', function() {
            validate_form();
        });
    };
    if (userfield != undefined) {
        userfield.addEventListener('input', function() {
            validate_form();
        });
    };
    if (oldpasswdfield != undefined) {
        oldpasswdfield.addEventListener('input', function() {
            validate_form();
        });
    };
});
