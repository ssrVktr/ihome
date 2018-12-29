$(function(){
    // 向后端获取城区信息
    $.get('api/v1.0/areas', function (resp) {
        if (resp.errno == '0'){
            // ok
            var areas = resp.data;
            //使用js模板
            var html = template('areas-tmpl', {areas: areas});
            $('#area-id').html(html);
        }else {
            alert(resp.errmsg);
        }
    }, 'json');

    // 提交房屋数据
    $('#form-house-info').submit(function (ev) {
        ev.preventDefault();

        // 获取表单中的数据，并且利用map函数转成字典形式
        var data = {};
        $('#form-house-info').serializeArray().map(function (x) {
            data[x.name] = x.value
        });

        // 获取设施信息, each的回调函数接受两个参数,索引值和元素
        var facility = [];
        $(':checked[name=facility]').each(function (index, x) {
            facility[index] = $(x).val()
        });

        // 将设施信息合并到房屋信息中
        data.facility = facility;

        // 像后端发送数据
        $.ajax({
            url: 'api/v1.0/houses/info',
            type: 'post',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': $.cookie('csrf_token')
            }
        }).done(function (resp) {
            if (resp.errno == '0'){
                //ok
                // 隐藏基本信息表单
                $('#form-house-info').hide();
                // 显示图片表单
                $('#form-house-image').show();
                // 设置图片表单中的house_id
                $('#house-id').val(resp.data.house_id);
            }
            else if (resp.errno == '4101'){
                // 用户未登录
                alert(resp.errmsg);
                location.href = 'login.html'
            }
            else {
                alert(resp.errmsg)
            }
        })
    });

    // 提交房屋图片
    $('#form-house-image').submit(function (ev) {
        ev.preventDefault();
        $(this).ajaxSubmit({
            url: 'api/v1.0/houses/image',
            type: 'post',
            dataType: 'json',
            headers: {
                'X-CSRFToken': $.cookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == '0'){
                    //ok
                    $('.house-image-cons').append('<img src="'+ resp.data.image_url +'" alt="房屋图片">')
                }
                else if (resp.errno == '4101'){
                    // 用户未登录
                    alert(resp.errmsg);
                    location.href = 'login.html'
                }
                else {
                    alert(resp.errmsg)
                }
            }
        })
    })
});