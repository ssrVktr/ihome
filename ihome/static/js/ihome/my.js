function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
        url: '/api/v1.0/sessions',
        type: 'delete',
        headers: {
            'X-CSRFToken': getCookie('csrf_token')
        },
        success: function (data) {
            if (data.errno == '0') {
                location.href = "/";
            }
        }
    })
}

$(document).ready(function(){
})