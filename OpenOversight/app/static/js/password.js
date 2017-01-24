$(document).ready(function() {
    var strength = {
        0: "Very Bad",
        1: "Bad",
        2: "Weak",
        3: "Good",
        4: "Strong"
    }
    var password = document.getElementById('password');
    var password2 = document.getElementById('password2');
    var meter = document.getElementById('password-strength-meter');
    var meter2 = document.getElementById('password-confirmation-meter');
    var text = document.getElementById('password-strength-text');

    function check_confirmation() {
        var val1 = password.value;
        var val2 = password2.value;
        if (val2 !== "") {
            if (val1 == val2) {
                meter2.value = 5;
                $(meter2).removeClass("badmeter").addClass("goodmeter");
            } else {
                meter2.value = 5;
                $(meter2).removeClass("goodmeter").addClass("badmeter");
            }
        } else {
            meter2.value = 0;
        }
    }

    password.addEventListener('input', function() {
        var val = password.value;
        var result = zxcvbn(val);
        meter.value = result.score +1;
        if (val !== "") {
            text.innerHTML = "Strength: " + strength[result.score];
        } else {
            text.innerHTML = "";
            meter.value = 0;
        }
        check_confirmation();
    });
    password2.addEventListener('input', function() {
        check_confirmation();
    });
});
