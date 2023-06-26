$(document).ready(function () {
    $('.toggle_button').click(function () {
        $('.closed_todo').toggle();
        var buttonHtml = $('.toggle_button').html();
        if (buttonHtml === '<h1>Geschlossene Todos ▲</h1>') {
            $('.toggle_button').html('<h1>Geschlossene Todos</h1>');
        } else {
            $('.toggle_button').html('<h1>Geschlossene Todos</h1>');
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

    $(".desc").each(function () {
        let descElement = $(this);
        let todoId = descElement.closest('li').data('todo-id');
        $.ajax({
            url: '/api/todo/' + todoId,
            method: 'GET',
            success: function (todo) {
                descElement.append('<div class="overlay">'
                    + '<h1>Beschreibung: </h1>'
                    + '<p>' + todo.description + '</p>'
                    + '</div>');
            },
            error: function () {
                console.log('Fehler beim Abrufen des Todos von der API: ' + this.error);
                descElement.append('<div class="overlay">'
                    + '<p>Fehler beim Abrufen der Beschreibung</p>'
                    + '</div>');
            }
        });
    });
});