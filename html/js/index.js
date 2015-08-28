document.getElementById("registration-form").addEventListener("submit", function(event){
    event.preventDefault();
    var $login = document.getElementById("registration-login");
    var $password = document.getElementById("registration-password");

    function finish_registration(response){
        if (response.errorcode == 0){
                window.location.href = "/chat.html";
            }
            else{
                var $textParagraph = $('p[name=registration-msg-block]');
                $textParagraph.text(response.reason);
                $textParagraph.css({color: "firebrick"});
            }
    }

    $.post("/registration", {login: $login.value, password: $password.value})
        .done(function (data) {
            finish_registration(data);
        })
        .fail(function(data){
            var $response = jQuery.parseJSON(data.responseText);
            finish_registration($response);
        });
});

document.getElementById("auth-form").addEventListener("submit", function(event){
    event.preventDefault();
    var $login = document.getElementById("auth-login");
    var $password = document.getElementById("auth-password");

    function finish_auth(response){
        if (response.errorcode == 0){
                window.location.href = "/chat.html";
            }
            else{
                var $textParagraph = $('p[name=auth-msg-block]');
                $textParagraph.text(response.reason);
                $textParagraph.css({color: "firebrick"});
            }
    }

    $.post("/auth", {login: $login.value, password: $password.value})
        .done(function(data){
            finish_auth(data)
        })
        .fail(function(data){
            var $response = jQuery.parseJSON(data.responseText);
            finish_auth($response);
        });
});