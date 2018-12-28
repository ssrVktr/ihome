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
    //查询用户的实名认证信息
    $.get('api/v1.0/users/auth', function (resp) {
        if (resp.errno == '0'){
            // 如果返回的数据中real_name与id_card不为null，表示用户已填写实名信息
            if (resp.data.real_name && resp.data.id_card){
                $('#real-name').val(resp.data.real_name);
                $('#id-card').val(resp.data.id_card);
                // 给input添加disabled属性，禁止用户修改
                $('#real-name').prop('disabled', true);
                $('#id-card').prop('disabled', true);
                // 隐藏提交保存按钮
                $("#form-auth>input[type=submit]").hide();
            }
        }
        else if (resp.errno == '4101'){
            //未登录
            alert(resp.errmsg);
            location.href = 'login.html'
        }
        else {
            alert(resp.errmsg)
        }
    }, 'json');

    //设置实名认证信息
    $('#form-auth').submit(function (event) {
        event.preventDefault();
        // 如果信息填写不完整， 提醒用户
        var realName = $('#real-name').val();
        var idCard = $('#id-card').val();
        if (realName == '' || idCard == ''){
            $('.error-msg').show();
            return false;
        }
        // 将表单的数据转换为json字符串
        var data = {
            'real_name': realName,
            'id_card': idCard
        };
        var jsonData = JSON.stringify(data);

        //向后端提交
        $.ajax({
            url: 'api/v1.0/users/auth',
            type: 'post',
            dataType: 'json',
            contentType: 'application/json',
            data: jsonData,
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            }
        }).done(function (resp) {
            if (resp.errno == '0'){
                //success
                $('.error-msg').hide();
                //显示保存成功的弹框
                showSuccessMsg();
                $("#real-name").prop("disabled", true);
                $("#id-card").prop("disabled", true);
                $("#form-auth>input[type=submit]").hide();
            }
            else if (resp.errno == '4101'){
            //未登录
            alert(resp.errmsg);
            location.href = 'login.html'
            }
            else {
                alert(resp.errmsg)
            }

        })


    })
});
