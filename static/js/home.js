$('#send').click(function() {
    // 修正文を取得
    let modifier = $('#modifier_input').val();
    if (modifier.length == 0) return
    $('#modifier_input').val('');
    // テーブルに追加
    $('#talk_table').append('<tr><td class="modifier"><div class="balloon1-right modifier"><p>' + modifier + '</p></div></td></tr>')
    // 画像のpathを取得
    let targetImgPath = $('#talk_table .image:last img').attr('src');
    console.log(modifier, targetImgPath)
    let data = {
        "modifier": modifier,
        "image_path": targetImgPath
    }
    let json = JSON.stringify(data);
    $('#talk_table').append('<tr class="image"><td><div class="balloon1-left"><p>・・・</p></div></td></tr>')
    scroll_into_bottom()
    $.ajax({
        type: 'post',
        url: '/dress',
        data: json,
        contentType: 'application/json',
        dataType: 'text'
    })
    .done(function(data) {
        console.log(data);
        $('#talk_table .balloon1-left:last').empty()
        $('#talk_table .balloon1-left:last').append('<img src="' + data + '" alt="">')
        $('#talk_table .balloon1-left:last img').on('load', function() {
            scroll_into_bottom();
        });
    })
    .fail(function(jqXHR, XMLHttpRequest, textStatus, errorThrown) {
        console.log(jqXHR.responseJSON)
        console.log(XMLHttpRequest.status);
        console.log(textStatus);
        console.log(errorThrown);
    })
})

const scroll_into_bottom = () => {
    let element = document.documentElement;
    let bottom = element.scrollHeight - element.clientHeight;
    window.scroll(0, bottom);
}