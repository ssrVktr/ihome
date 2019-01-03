$(function () {
    // 对于发布房源，只有认证后的用户才可以，所以先判断用户的实名认证状态
    $.ajax({
        url: '/api/v1.0/users/auth',
        type: 'get',
        dataType: 'json'
    }).done(function (resp) {
        if (resp.errno == '0'){
            // 未认证的用户，在页面中展示 "去认证"的按钮
            if (!(resp.data.real_name && resp.data.id_card)){
                $(".auth-warn").show();
                $('.new-house').hide();
            }
            else {
                $(".auth-warn").hide();
                $.ajax({
                    url: '/api/v1.0/user/houses',
                    type: 'get',
                    dataType: 'json'
                }).done(function (resp) {
                    if (resp.errno == '0'){
                        var html = template('houses-list-tmpl', {houses: resp.data.houses});
                        $('#houses-list').html(html)
                    }

                })
            }
        }// 用户未登录
        else if (resp.errno == '4101') {
            alert(resp.errmsg);
            location.href = 'login.html'
        }
        else {
            alert(resp.errmsg)
        }
    })

    
})