$(document).ready(function () {
    //$('.closed_todo').hide();
    $('.toggle_button').click(function () {
        $('.closed_todo').toggle();
        var buttonHtml = $('.toggle_button').html();
        if (buttonHtml === '<h1>Geschlossene Todos ▲</h1>') {
            $('.toggle_button').html('<h1>Geschlossene Todos ▼</h1>');
        } else {
            $('.toggle_button').html('<h1>Geschlossene Todos ▲</h1>');
        }
    });
    $('.filter').change(function () {
        var selectedOption = $(this).children("option:selected").val();
        $.ajax({
            type: "POST",
            url: "/filter/" + selectedOption,
            success: function () {
                location.reload();
            }
        });
    });
});