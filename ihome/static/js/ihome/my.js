function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 退出登录
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


$(function () {
    // 打开页面后获取用户的用户名和手机号
   $.ajax({
       url: 'api/v1.0/users/center',
       type: 'get',
       dataType: 'json',
       success: function (data) {
           if (data.errno == '0'){
               //获取成功
               var userName = data.data.user_name
               var mobile = data.data.mobile
               $('#user-name').html(userName)
               $('#user-mobile').html(mobile)
           }
           else if (data.errno == '4101'){
               alert(data.errmsg)
               location.href = 'login.html'
           }
           else {
               alert(data.errmsg)
           }

       }
   })
});