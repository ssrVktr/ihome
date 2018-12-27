function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){});
        },1000)
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    // 获取用户头像
    $.ajax({
        url: 'api/v1.0/users/avatar',
        type: 'get',
        dataType: 'json',
        success: function (data) {
            if(data.errno == '0'){
                var avatarUrl = data.data.avatar_url
                $('#user-avatar').prop('src', avatarUrl)
            }
            else if(data.errno == '4101'){
                alert(data.errmsg);
                location.href = 'login.html'
            }
            else {
                alert(data.errmsg)
            }
        }
    });

    // 获取用户昵称
    $.ajax({
        url: 'api/v1.0/users/user_name',
        type: 'get',
        dataType: 'json',
        success: function (data) {
            if (data.errno == '0'){
                //查询成功
                var userName = data.data.user_name;
                $('#user-name').val(userName)
            }
            else if(data.errno == '4101'){
                alert(data.errmsg);
                location.href = 'login.html'
            }
            else {
                alert(data.errmsg)
            }

        }
    });

    // 更新用户头像
    $('#form-avatar').submit(function (event) {
       event.preventDefault();
       $(this).ajaxSubmit({
           url: 'api/v1.0/users/avatar',
           type: 'post',
           dataType: 'json',
           headers: {
               'X-CSRFToken': getCookie('csrf-token')
           },
           success: function (data) {
               if (data.errno == '0'){
                   // 上传成功
                   var avatarUrl = data.data.avatar_url;
                   $('#user-avatar').prop('src', avatarUrl)
                   showSuccessMsg()
               } else {
                   alert(data.errmsg);
               }
           }
       })

    });

    //更新用户昵称

    $('#form-name').submit(function (event) {
        event.preventDefault();
        var newName = $('#user-name').val();
        var req_data = {
            'new_user_name': newName
        };
        var req_json = JSON.stringify(req_data);
        $.ajax({
            url: 'api/v1.0/users/user_name',
            type: 'post',
            data: req_json,
            contentType: 'application/json',
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '0'){
                    //保存成功
                    showSuccessMsg()
                }
                else if (data.errno == '4003'){
                    $('.error-msg').show();
                }
                else{
                    alert(data.errmsg)
                }

            }
        })
    })



});

