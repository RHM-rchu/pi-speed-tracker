$(document).ready(function() {
    $('.showModal').click(function(e) {
        // var id = $(this).attr('id');
        var cur_img = $(this).data('id');
        var cur_txt = $(this).attr('alt');
        $("#myImage").attr("src", cur_img);
        document.getElementById('modal_caption').innerHTML = cur_txt
        $("#modal").show();

        show_next_prev_or_not()
    });
    $('.hideModal').click(function() {
        $("#modal").hide();
    });
    // https://jsfiddle.net/6h20cdrx/
    $('div .next_img').click(function() {
        var myImageId = $("#myImage").attr('src');

        var nextObj = $('a[data-id="' + myImageId + '"]').closest('tr').next('tr').find("a");
        var next_img = nextObj.attr('data-id');
        var next_txt = nextObj.attr('alt');
        // hack bc sometime cars are so close together they have the same img names. need to address in app
        if (next_img === myImageId ) {
            console.log(`two images named ${next_img} found, advaancing by 2 cells`)
            var nextTR = $('a[data-id="' + myImageId + '"]').closest('tr').nextAll('tr')[1];
            var nextObj = $(nextTR).find("a");
            var next_img = nextObj.attr('data-id');
            var next_txt = nextObj.attr('alt');
        }
        if(next_img == undefined) {
            return null
        } 
        // var next_row = $('a[data-id="' + myImageId + '"]').closest('tr').index();
        $("#myImage").attr("src", next_img);
        document.getElementById('modal_caption').innerHTML = next_txt

        show_next_prev_or_not()

    });
    $('div .prev_img').click(function() {
        var myImageId = $('#myImage').attr('src');

        var prevObj = $('a[data-id="' + myImageId + '"]').closest('tr').prev('tr').find("a");
        var prev_img = prevObj.attr('data-id');
        var prev_txt = prevObj.attr('alt');
        $("#myImage").attr("src", prev_img);
        document.getElementById('modal_caption').innerHTML = prev_txt

        show_next_prev_or_not()
    });

    // next prev
    function show_next_prev_or_not(myImageId) {
        var myImageId = $('#myImage').attr('src');
        var prev_img = $('a[data-id="' + myImageId + '"]').closest('tr').prev('tr').find("a").attr('data-id');
        if (typeof prev_img == 'undefined') {
            $("div #prev_img").hide();
        } else {
            $("div #prev_img").show();
        }
        var next_img = $('a[data-id="' + myImageId + '"]').closest('tr').next('tr').find("a").attr('data-id');
        if (typeof next_img == 'undefined') {
            $("div #next_img").hide();
        } else {
            $("div #next_img").show();
        }
    }
});